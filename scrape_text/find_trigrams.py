import random
import time
import re
import threading
import requests
import yaml
from bs4 import BeautifulSoup
import urllib.parse

WEB_PROTOCOL = "https"
WEB_SUBDOMAIN = "en"
WEB_DOMAIN = "wikipedia"
WEB_HOST = "org"

thread_count = 1
thread_lock = threading.Lock()
delay = 1
links = []

full_trigrams = {}

def build_url(path):
  base = f"{WEB_PROTOCOL}://{WEB_SUBDOMAIN}.{WEB_DOMAIN}.{WEB_HOST}"
  return base + path

def shift_left(arr):
  for i in range(1, len(arr)):
    arr[i - 1] = arr[i]

def find_trigrams(index):
  trigrams = {}

  # find trigrams until no more pages are left
  while len(links[index]) > 0:
    url = links[index].pop()
    
    res = requests.get(url, allow_redirects=False)
    status = res.status_code

    # valid status code: 200 - 299
    if int(status / 100) != 2:
      print(f"Response [{status}] on page: {url}!")
      continue

    soup = BeautifulSoup(res.text, "html.parser")

    container = soup.find(id="bodyContent").find_all("p")

    for paragraph in container:
      # gather and clean the text
      text = paragraph.get_text(separator=" ", strip=True)
      text = re.sub(r"\[ \d+ \]", "", text)

      # traverse through every word
      prev_tokens = []
      for word in re.findall(r"\w+|[^\w\s\d]|\d+", text):
        # if word is empty, move on
        if word == "":
          continue

        # append the word to prev tokens if there are not enough
        if len(prev_tokens) < 3:
          prev_tokens.append(word)
        else: # shift prev_tokens if it is full
          shift_left(prev_tokens)
          prev_tokens[2] = word

        # if not enough, move on
        if len(prev_tokens) < 3:
          continue

        key = (prev_tokens[0], prev_tokens[1], prev_tokens[2])
        if key in trigrams:
          trigrams[key] += 1
        else:
          trigrams[key] = 1
    
    print(f"Thread {index} processed a page! {len(links[index])} left!")
    time.sleep(delay)
  
  # filter the trigrams
  trigrams = dict(filter(lambda item: item[1] >= filter_threshold, trigrams.items()))

  print(f"Thread {index} waiting to join trigrams!")
  # join all the trigrams
  with thread_lock:
    print(f"Thread {index} joining trigrams!")
    for trigram in trigrams:
      if trigram in full_trigrams:
        full_trigrams[trigram] += trigrams[trigram]
      else:
        full_trigrams[trigram] = trigrams[trigram]

if __name__ == "__main__":
  scrape_probability = 1
  filter_threshold = 0
  # read the config file
  with open("./configs/trigrams_config.yaml", "r") as file:
    configs = yaml.load(file, Loader=yaml.FullLoader)
    thread_count = int(configs["thread_count"])
    delay = float(configs["delay"])
    scrape_probability = float(configs["scrape_probability"])
    filter_threshold = float(configs["filter_threshold"])

  # prepare all the global variables
  for thread in range(thread_count):
    links.append([])

  # read the list of pages
  with open("./data/wikipedia_pages.txt", "r") as file:
    for i, line in enumerate(file):
      # the first line indicate the number of pages
      if i == 0:
        continue

      # assign the pages to the threads evenly
      if random.random() < scrape_probability:
        cleaned_url = urllib.parse.quote(line, safe="/:#").rstrip("%0A")
        links[i % thread_count].append(build_url(cleaned_url))

  threads = []
  for i in range(thread_count):
    trigram_thread = threading.Thread(target=find_trigrams, args=[i])
    threads.append(trigram_thread)
    trigram_thread.start()
  
  for thread in threads:
    thread.join()

  # store the trigrams in a file
  with open("./data/trigrams.txt", "w") as file:
    file.write(f"Found {len(full_trigrams)} trigrams!\n")
    for trigram in full_trigrams:
      file.write(f"{full_trigrams[trigram]} {trigram}\n")
