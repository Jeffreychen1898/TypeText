import os
import time
import struct
import urllib.parse
import random
import yaml

from worker.utils import response_ok

# TODO: get_trigram_word, get_trigram_edges, implement get_trigram, implement generate_text
# TODO: get_trigram, error checking if server doesn't contain data from that partition
# text_cache_arr = thread safe array. generate text should be sent to multi threads
# fault tolerance when: worker server shutdown, worker server reject request,
# manager server shutdown, manager server reject request

class TrigramPartitions:
    def __init__(self):
        self.num_partitions = int(os.getenv("NUM_PARTITIONS"))
        self.request_timeout_time = 5
        self.host = os.getenv("HOST")
        self.port = os.getenv("PORT")

        self.trigram_distribution = []
        self.services = []
        self.partitions = [[] for _ in range(self.num_partitions)]

        self.trigrams = [None for _ in range(self.num_partitions)]
        self.graphs = [None for _ in range(self.num_partitions)]

        self.load_trigram_distribution("./partition_config.yaml")
        self.load_configs("./config.yaml")

        self.add_service({
            "host": self.host,
            "port": self.port,
            "partitions": [i for i, val in enumerate(self.trigrams) if val is not None],
        })
        self.generate_text()

    def add_service(self, server):
        service_index = len(self.services)
        self.services.append(server)
        for partition in server["partitions"]:
            self.partitions[partition].append(service_index)

    def remove_service(self, index):
        for partition in self.services[index]["partitions"]:
            self.partitions[partition].remove(index)

        self.services.pop(index)

    def load_configs(self, filepath):
        with open(filepath, "r") as file:
            configs = yaml.load(file, Loader=yaml.FullLoader)
            for partition in configs["partitions"]:
                partition_id = partition["partition"]
                trigram_words = self.load_trigram_words(partition["trigrams"])
                self.trigrams[partition_id] = {
                    "metadata": trigram_words[0],
                    "trigrams": trigram_words[1],
                }
                self.graphs[partition_id] = self.load_trigram_graph(partition["graph"])

    def load_trigram_distribution(self, filepath):
        with open(filepath, "r") as file:
            configs = yaml.load(file, Loader=yaml.FullLoader)
            for target_file in configs["id_lookup"]:
                file_range = configs["id_lookup"][target_file].split("-")
                self.trigram_distribution.append({
                    "file": target_file,
                    "begin": int(file_range[0]),
                    "end": int(file_range[1]),
                })

        self.trigram_distribution.sort(key=lambda elem: elem["begin"])

    def load_trigram_words(self, filepath):
        trigram_metadata = []
        trigram_data = []
        with open(filepath, "rb") as file:
            # load in the number of trigrams in the file
            num_trigrams = file.read(8)
            num_trigrams = struct.unpack("q", num_trigrams)[0]
            file.seek(9)

            trigram_data = ["" for _ in range(num_trigrams)]

            # load in the metadata of all the trigrams
            for i in range(num_trigrams):
                metadata = file.read(9)
                frequency = struct.unpack("q", metadata[:8])[0]
                length = metadata[-1]
                trigram_metadata.append({
                    "frequency": frequency,
                    "length": length,
                })

            # load in the trigrams chunk by chunk
            chunk_bytes = file.read(9)
            i = 0
            while chunk_bytes:
                chunk = struct.unpack("9s", chunk_bytes)[0].decode()
                trigram_data[i] += chunk

                chunk_bytes = file.read(9)
                i = (i + 1) % len(trigram_data)

        for i, trigram in enumerate(trigram_data):
            trigram_data[i] = trigram.rstrip("#").split("#")

        return (trigram_metadata, trigram_data)

    def load_trigram_graph(self, filepath):
        graph = []
        with open(filepath, "rb") as file:
            # load in the number of vertices/nodes in this graph partition
            num_nodes = file.read(8)
            num_nodes = struct.unpack("q", num_nodes)[0]

            file.seek(24)

            for i in range(num_nodes):
                node_data_bytes = file.read(24)
                node_data = struct.unpack("qqq", node_data_bytes)
                graph.append(node_data)

        return graph

    def get_partition(self, trigramid):
        l = 0
        r = len(self.trigram_distribution) - 1
        while l <= r:
            middle = (l + r) // 2
            if trigramid > self.trigram_distribution[middle]["end"]:
                l = middle + 1
                continue

            if trigramid < self.trigram_distribution[middle]["begin"]:
                r = middle - 1
                continue

            return middle

        return -1

    def get_available_service(self, partition):
        # check if there are services that serve this partition
        num_available = len(self.partitions[partition])
        if num_available == 0:
            return None

        # check if current server serve this partition
        if self.partitions[partition][0] == 0:
            return {}

        # choose a random service
        random_service = random.randint(0, num_available - 1)
        service_index = self.partitions[partition][random_service]

        return self.services[service_index]

    def get_trigram_word(self, partition, id):
        id_start = self.trigram_distribution[partition]["begin"]
        trigram_word = self.trigrams[partition]["trigrams"][id - id_start]
        trigram_frequency = self.trigrams[partition]["metadata"][id - id_start]
        return (trigram_word, trigram_frequency)

    def get_trigram_edges(self, partition, id):
        id_start = self.trigram_distribution[partition]["begin"]
        edge_id = self.graphs[partition][id - id_start][1]
        num_edges = self.graphs[partition][id - id_start][2]
        return (edge_id, num_edges)

    def get_trigram(self, id):
        partition = self.get_partition(id)
        if partition == -1:
            return {}

        trigram_word, trigram_frequency = self.get_trigram_word(partition, id)
        trigram_edges, num_edges = self.get_trigram_edges(partition, id)

        return {
            "trigram": trigram_word,
            "frequency": trigram_frequency["frequency"],
            "edge_id": trigram_edges,
            "num_edges": num_edges,
        }

    def retrieve_trigram(self, id):
        # IDEA: if a service is not responding, they are not necessarily down
        partition = self.get_partition(id)
        if partition == -1:
            return {}

        available_service = self.get_available_service(partition)
        while available_service is not None:
            # redirect call to get_trigram if current server has what is needed
            if available_service == {}:
                return self.get_trigram(id)

            # send get request
            try:
                response = requests.get(available_service["host"], timeout=self.request_timeout_time)
                if response_ok(response.status_code):
                    return response.json()
            except:
                pass

            # try again, maybe with a new service
            available_service = self.get_available_service(partition)
            time.sleep(0.1)

    def sample_random_trigram(self):
        rand_partition = random.choice(self.services[0]["partitions"])
        partition_start = self.trigram_distribution[rand_partition]["begin"]

        rand_trigram = random.randint(0, len(self.graphs[rand_partition]) - 1)

        return (rand_trigram + partition_start, rand_partition, rand_trigram)

    def generate_text(self):
        # choose the seed, random trigram
        final = []
        for j in range(50):
            (start_id, start_partition, start_index) = self.sample_random_trigram()
            sequence = [{
                "trigram": [start_partition, start_index],
                "id": start_id,
                "edges": self.graphs[start_partition][start_index],
            }]
            for i in range(50):
                if sequence[-1]["edges"][2] == 0:
                    break

                next_trigram_id = random.randint(0, sequence[-1]["edges"][2] - 1) + sequence[-1]["edges"][1]
                next_trigram_partition = self.get_partition(next_trigram_id)
                id_start = self.trigram_distribution[next_trigram_partition]["begin"]
                sequence.append({
                    "trigram": [next_trigram_partition, next_trigram_id - id_start],
                    "id": next_trigram_id,
                    "edges": self.graphs[next_trigram_partition][next_trigram_id - id_start],
                })
            if len(sequence) > len(final):
                final = sequence

        trigram_text = ""
        for elem in final:
            elem_partition = elem["trigram"][0]
            elem_id = elem["id"]
            elem_trigrams = self.get_trigram_word(elem["trigram"][0], elem["id"])[0]
            if trigram_text == "":
                trigram_text += f"{elem_trigrams[0]} {elem_trigrams[1]} "
            trigram_text += f"{elem_trigrams[2]} "
            print(elem_trigrams)

        print()
        print(urllib.parse.unquote(trigram_text))

    def is_home_service(self, service):
        try:
            if service["host"] != self.services[0]["host"]:
                return False
            if service["port"] != self.services[0]["port"]:
                return False

            return True
        except:
            return False
