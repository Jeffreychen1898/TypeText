import struct
import argparse

# in bytes
FORMAT_STRIDE = 8
FORMAT_OFFSET = 8
TRIGRAM_LEN_BYTES = 1

def format_trigram(trigram):
  trigram_str = trigram[0] + "#" + trigram[1] + "#" + trigram[2]
  buffer = [""]

  for c in trigram_str:
    if len(buffer[-1]) < (FORMAT_STRIDE + TRIGRAM_LEN_BYTES):
      buffer[-1] += c
    else:
      buffer.append(c)
  
  # ensure constant size
  chunk_gap = (FORMAT_STRIDE + TRIGRAM_LEN_BYTES) - len(buffer[-1])
  if chunk_gap > 0:
    buffer[-1] += "#" * chunk_gap

  buffer.reverse()

  return buffer, len(trigram_str)

if __name__ == "__main__":
  trigrams = {}

  # parse the command line arguments
  parser = argparse.ArgumentParser()
  parser.add_argument("input", type=str, help="The input trigrams file to format!")
  parser.add_argument("output", type=str, help="The formatted output file!")

  args = parser.parse_args()

  # open the input file and load in all the trigrams
  with open(args.input, "r") as file:
    for line in file:
      word1, word2, word3, freq = line.split("#")
      key = (word1, word2, word3)
      if key in trigrams:
        trigrams[key] += int(freq)
      else:
        trigrams[key] = int(freq)

  # calculate all the bytes
  trigrams_freq = []
  trigrams_data_size = []
  trigrams_data = []
  for key, value in sorted(trigrams.items()):
    freq_bytes = struct.pack("q", value)
    trigram_data, trigram_len = format_trigram(key)
    trigram_len_bytes = struct.pack("B", trigram_len)
    trigram_data_bytes = []
    for chunk in trigram_data:
      chunk_bytes = struct.pack(f"{FORMAT_STRIDE + TRIGRAM_LEN_BYTES}s", chunk.encode())
      trigram_data_bytes.append(chunk_bytes)
    
    trigrams_freq.append(freq_bytes)
    trigrams_data_size.append(trigram_len_bytes)
    trigrams_data.append(trigram_data_bytes)

  # write the data to a binary file
  num_cols = len(trigrams)
  with open(args.output, "wb") as file:
    # write the size (64 bits, 8 bytes)
    size_bin = struct.pack("q", len(trigrams))
    file.write(size_bin)
    file.seek(9)

    print("Writing trigram frequencies!")
    # print the frequency and length of each trigram
    for freq, size in zip(trigrams_freq, trigrams_data_size):
      file.write(freq)
      file.write(size)

    print("Writing trigram length!")
    # print the data of each trigram
    dummy_chunk = "#" * (FORMAT_STRIDE + TRIGRAM_LEN_BYTES)
    dummy_bytes = struct.pack(f"{FORMAT_STRIDE + TRIGRAM_LEN_BYTES}s", dummy_chunk.encode())

    print("Writing trigram data!")
    while True:
      has_chunks = False
      for chunk_arr in trigrams_data:
        chunk = dummy_bytes
        if len(chunk_arr) > 0:
          chunk = chunk_arr.pop()
        if len(chunk_arr) > 0:
          has_chunks = True

        file.write(chunk)
      
      print("Written a trigram chunk!")
      
      if not has_chunks:
        break
  
  print(f"Written {len(trigrams)} Trigrams!")