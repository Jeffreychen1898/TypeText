import urllib.parse
import yaml

input_files = []
output_files = []

trigrams_base = []
case_sensitive = False

def sort_file(path, writemode):
  trigrams = trigrams_base.copy()
  section_index = 0

  with open(path, "r") as file:
    for i, line in enumerate(file):
      # skip the first line
      if i == 0:
        continue

      # get the trigram words and frequency
      count, word1, word2, word3 = line.split()
      count = int(count)

      # validate these words are ascii
      if "\\u" in word1 or "\\u" in word2 or "\\u" in word3:
        continue
      try:
        word1[2:-2].encode("ascii")
        word2[1:-2].encode("ascii")
        word3[1:-2].encode("ascii")
      except UnicodeEncodeError:
        continue

      # encode the words
      if not case_sensitive:
        word1 = word1.lower()
        word2 = word2.lower()
        word3 = word3.lower()

      word1 = urllib.parse.quote(word1[2:-2])
      word2 = urllib.parse.quote(word2[1:-2])
      word3 = urllib.parse.quote(word3[1:-2])

      trigram_str = (word1, word2, word3, str(count))
      trigrams.append(trigram_str)

  # sort the trigrams array
  trigrams = sorted(trigrams, key=lambda x: "".join(x), reverse=True)

  # store the trigrams in the proper files
  store_file = open(
    f"{output_files[0]}{section_index}{output_files[1]}",
    writemode
  )
  while len(trigrams) > 0:
    smallest = trigrams.pop()
    
    # if we encounter a separator, load up the next file
    if len(smallest) == 1:
      section_index += 1
      store_file.close()
      if len(trigrams) > 0:
        store_file = open(
          f"{output_files[0]}{section_index}{output_files[1]}",
          writemode
        )
      else:
        store_file = None

      continue

    # write to the file
    trigram_string = "#".join(smallest)
    store_file.write(f"{trigram_string}\n")
  
  if store_file is not None:
    store_file.close()

if __name__ == "__main__":
  separators = []
  # read config files
  with open("./configs/separator_config.yaml", "r") as file:
    configs = yaml.load(file, Loader=yaml.FullLoader)
    input_files = configs["files"]
    separators = configs["separators"]
    output_files = configs["output"].split()
    case_sensitive = configs["case_sensitive"]
  
  # store the separators in the trigrams_base
  for separator in separators:
    cleaned_separator = separator.lstrip("\\")
    trigrams_base.append((cleaned_separator,))

  # sort all the files
  for i, file in enumerate(input_files):
    writemode = "a"
    if i == 0:
      writemode = "w"
    
    sort_file(file, writemode)
    print(f"Finished sorting file: {file}")