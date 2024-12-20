import struct
import argparse
import yaml

# issue: neighboring vertices are in different files

separators = []
partition_files = []

def load_trigrams(path):
  with open(path, "rb") as file:
    num_trigrams_bytes = file.read(9)
    num_trigrams = struct.unpack("q", num_trigrams_bytes[:-1])[0]

    freqs = []
    lengths = []
    # read the frequencies and trigram length
    for i in range(num_trigrams):
      metadata_bytes = file.read(9)
      freq = struct.unpack("q", metadata_bytes[:-1])[0]
      length = metadata_bytes[-1]
      freqs.append(freq)
      lengths.append(length)

    # read the trigrams
    trigram_packets = ["" for _ in range(num_trigrams)]
    while True:
      should_terminate = False
      for i in range(num_trigrams):
        packet_bytes = file.read(9)
        if not packet_bytes:
          should_terminate = True
          break

        packet_data = struct.unpack("9s", packet_bytes)[0].decode()
        trigram_packets[i] += packet_data

      if should_terminate:
        break

    # putting it all together
    trigrams = [(f, l, s.rstrip("#").split("#")) for f, l, s in zip(freqs, lengths, trigram_packets)]

    return trigrams

def partition(separators, trigrams):
  partitioned = [[]]
  partition_idx = 0
  for trigram in trigrams:
    key = "".join(trigram[2][1:])
    while partition_idx < len(separators) and not key < separators[partition_idx]:
      partition_idx += 1
      partitioned.append([])

    partitioned[partition_idx].append(trigram)

  return partitioned

def convert_to_dict(arr):
  trigram_dict = {}
  for i, item in enumerate(arr):
    key = (item[2][0], item[2][1])
    trigram = [i, item[0], item[1], item[2]]
    if key in trigram_dict:
      trigram_dict[key].append(trigram)
    else:
      trigram_dict[key] = [trigram]

  return trigram_dict

if __name__ == "__main__":
  # retrieve the command line arguments
  parser = argparse.ArgumentParser()
  parser.add_argument("config", type=str, help="The path to the configuration file!")
  parser.add_argument("input", type=str, help="The path to the input trigrams file!")
  parser.add_argument("output", type=str, help="The path of the output graph file!")
  parser.add_argument("-l", "--label", action="store_true", help="Use flag to enable generating a label file!")

  args = parser.parse_args()

  # retrieve the config file data
  with open(args.config, "r") as file:
    configs = yaml.load(file, Loader=yaml.FullLoader)
    partition_files = configs["partitions"]
    separators_tokens = configs["separators"]
    for token in separators_tokens:
      separators.append(token.lstrip("\\"))

  # load and sort input file trigrams
  trigrams = load_trigrams(args.input)

  trigrams_ordered = trigrams.copy()
  trigrams.sort(key=lambda x: "#".join(x[2][1:]))
  separators.sort()

  # partition trigrams based on edges lookup file
  partitioned_trigrams = partition(separators, trigrams)

  lookup_size = [0]
  id_accum = 0
  neighbors = {}

  for i, partition in enumerate(partitioned_trigrams):
    # update id accum and load up the necessary files
    id_accum += lookup_size[-1]
    lookup_trigrams = load_trigrams(partition_files[i])
    lookup_size.append(len(lookup_trigrams))

    if len(partition) == 0:
      continue

    lookup_trigrams = convert_to_dict(lookup_trigrams)

    for trigram in partition:
      key = (trigram[2][1], trigram[2][2])
      if key not in lookup_trigrams:
        continue # end of sequence

      neighbor_start = lookup_trigrams[key][0][0]
      freqs = [each[1] for each in lookup_trigrams[key]]
      neighbors["#".join(trigram[2])] = (neighbor_start + id_accum, freqs, lookup_trigrams[key][0])

    print(f"Finished partition {i}!")

  # write the graph into the output file
  with open(args.output, "wb") as file:
    # write the metadata
    num_nodes = struct.pack("q", len(trigrams))
    file.write(num_nodes)
    file.seek(24)

    # write the id and freq sum of each node
    for trigram in trigrams_ordered:
      key = "#".join(trigram[2])
      trigram_freq = trigram[0]
      neighbor_id = 0
      num_neighbors = 0

      if key in neighbors:
        neighbor_id = neighbors[key][0]
        num_neighbors = len(neighbors[key][1])

      freq_bytes = struct.pack("q", trigram_freq)
      neighbor_id_bytes = struct.pack("q", neighbor_id)
      num_neighbors_bytes = struct.pack("q", num_neighbors)

      file.write(freq_bytes)
      file.write(neighbor_id_bytes)
      file.write(num_neighbors_bytes)

  # write the labels of the which id corresponding to which file
  if args.label:
    total_nodes = id_accum + lookup_size[-1]
    config_data = {
      "total_nodes": total_nodes,
      "id_lookup": {}
    }
    id_accum = 0
    for i, filelen in enumerate(lookup_size[1:]):
      config_data["id_lookup"][partition_files[i]] = f"{id_accum}-{id_accum + filelen - 1}"
      id_accum += filelen

    with open("./graph_config.yaml", "w") as file:
      file.write(yaml.dump(config_data))
    
    print("Written the id lookup labels to the file: ./graph_config.yaml!")
