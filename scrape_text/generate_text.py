import random
import urllib.parse
import struct

graph = []

def find_range(ranges, num):
  # small number of elems anyways, too lazy to binary search
  for i, r in enumerate(ranges):
    small = r[0]
    big = r[1]
    if num >= small and num <= big:
      return i

  return -1


def lookup_trigram(file_id, idx):
  chunks = []
  with open(f"./data/trigrams-f-{file_id}.bin", "rb") as file:
    num_trigrams_bytes = file.read(8)
    num_trigrams = struct.unpack("q", num_trigrams_bytes)[0]

    file.seek(9 + idx * 9)
    # read the frequency and len
    metadata_bytes = file.read(9)
    length = metadata_bytes[-1]

    for i in range(0, length, 9):
      row = i // 9 + 1
      file.seek((row * num_trigrams + idx) * 9 + 9)
      chunk_bytes = file.read(9)
      chunk_data = struct.unpack("9s", chunk_bytes)[0].decode()
      chunks.append(chunk_data)

  return "".join(chunks)

# load up all the graphs
for i in range(19):
  with open(f"./data/graph-{i}.bin", "rb") as file:
    num_nodes_bytes = file.read(8)
    num_nodes = struct.unpack("q", num_nodes_bytes)[0]

    file.seek(24)

    for i in range(num_nodes):
      freq_bytes = file.read(8)
      neighbor_id_bytes = file.read(8)
      num_neighbors_bytes = file.read(8)

      freq = struct.unpack("q", freq_bytes)[0]
      neighbor_id = struct.unpack("q", neighbor_id_bytes)[0]
      num_neighbors = struct.unpack("q", num_neighbors_bytes)[0]

      graph.append((freq, neighbor_id, num_neighbors))

print("generating sequence")
# generate a sequence
seq_len = 100
sequence = []
for j in range(50):
  start_node = int(random.random() * 2945610)
  subsequence = [start_node]
  for i in range(seq_len - 1):
    freq, neighbor, num_neighbors = graph[subsequence[-1]]
    if num_neighbors == 0:
      break

    # next_node = neighbor
    # freqs_lst = [graph[i + neighbor][0] for i in range(num_neighbors)]
    # rand_val = int(random.random() * sum(freqs_lst))
    # for k, f in enumerate(freqs_lst):
    #   if rand_val < f:
    #     next_node += k
    #     break
    #   rand_val -= f
    next_node = int(random.random() * num_neighbors) + neighbor
    subsequence.append(next_node)

  if len(subsequence) > len(sequence):
    sequence = subsequence

id_ranges = [
  [0,153694],
  [153695,267836],
  [267837,415917],
  [415918,586513],
  [586514,795055],
  [795056,981257],
  [981258,1184959],
  [1184960,1363524],
  [1363525,1508463],
  [1508464,1684981],
  [1684982,1854077],
  [1854078,1990007],
  [1990008,2149628],
  [2149629,2294550],
  [2294551,2467056],
  [2467057,2634436],
  [2634437,2790972],
  [2790973,2913055],
  [2913056,3070614],
]

# reading the tokens
text = []
for node in sequence:
  r = find_range(id_ranges, node)
  relative_id = node - id_ranges[r][0]
  trigram = lookup_trigram(r, relative_id)

  trigrams = trigram.rstrip("#").split("#")
  for i, each in enumerate(trigrams):
    if each[0] == "%":
      trigrams[i] = urllib.parse.unquote(each)

  if len(text) == 0:
    text.append(trigrams[0])
    text.append(trigrams[1])
  text.append(trigrams[2])
  print(trigram)

print(" ".join(text))