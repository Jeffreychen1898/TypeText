import requests
from bs4 import BeautifulSoup
import threading
from collections import deque
import re
import yaml
import time
import urllib.parse

# soft page count, can go over
PAGE_COUNT = 5000

WEB_PROTOCOL = "https"
WEB_SUBDOMAIN = "en"
WEB_DOMAIN = "wikipedia"
WEB_HOST = "org"

delay = 1
thread_lock = threading.Lock()

found = set()
discovered = deque()

def build_url(path):
  base = f"{WEB_PROTOCOL}://{WEB_SUBDOMAIN}.{WEB_DOMAIN}.{WEB_HOST}"
  return base + path

def validate_format(path):
  return re.match("^/wiki/[^/:]*$", path) is not None

def scrape_thread(index):
  found_pages = []

  while len(found) < PAGE_COUNT:
    # find the next page to process
    process_page = None
    with thread_lock:
      if len(discovered) > 0:
        process_page = discovered.popleft()
    
    if process_page is None:
      time.sleep(delay)
      continue

    # request the documents
    process_page = build_url(process_page)
    response = requests.get(process_page)
    status = response.status_code

    # valid status code: 200 - 299
    if int(status / 100) != 2:
      print("Response [{status}] on page: {process_page}!")
      continue

    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a", href=True)

    for link in links:
      path = urllib.parse.unquote(link["href"])
      if validate_format(path):
        found_pages.append(path)

    with thread_lock:
      for page in found_pages:
        # ignore pages that are already discovered
        if page in found:
          continue

        # append the page in the list of discovered pages
        discovered.append(page)
        found.add(page)

      found_pages.clear()
      print(f"{len(found)} pages found!")
    
    time.sleep(delay) # limit the rate in which requests are sent

if __name__ == "__main__":
  with open("./configs/scrape_config.yaml", "r") as file:
    # read the config files
    configs = yaml.load(file, Loader=yaml.FullLoader)

    thread_count = configs["thread_count"]
    delay = configs["delay"]
    root_pages = configs["root_pages"]

    # append the root pages
    for page in root_pages:
      found.add(page)
      discovered.append(page)
    
    # start the threads
    threads = []
    for i in range(thread_count):
      thread = threading.Thread(target=scrape_thread, args=[i])
      thread.start()
      threads.append(thread)
    
    # join the threads
    for thread in threads:
      thread.join()
    
    print(f"Found {len(found)} pages!")

    # store the pages in a file
    with open("wikipedia_pages.txt", "w") as file:
      print(f"Found {len(found)} pages!")
      for page in found:
        file.write(f"{page}\n")
