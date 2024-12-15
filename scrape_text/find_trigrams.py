import re
import requests
from bs4 import BeautifulSoup

pairs = {}
sentence_ending_tokens = set(". ! ? :".split(" "))

res = requests.get("https://en.wikipedia.org/wiki/MMORPGs")
soup = BeautifulSoup(res.text, "html.parser")

def shift_left(arr):
  for i in range(1, len(arr)):
    arr[i - 1] = arr[i]

container = soup.find(id="bodyContent").find_all("p")
for paragraph in container:
  text = paragraph.get_text(separator=" ", strip=True)
  cleaned = re.sub(r"\[ \d+ \]", "", text)

  prev_tokens = []
  for word in re.findall(r"\w+|[^\w\s\d]|\d+", cleaned):
    if word == "":
      continue
    if len(prev_tokens) < 2:
      prev_tokens.append(word)
      continue

    if len(prev_tokens) < 3:
      prev_tokens.append(word)
    else:
      shift_left(prev_tokens)
      prev_tokens[2] = word

    key = (prev_tokens[0], prev_tokens[1], prev_tokens[2])

    if key in pairs:
      pairs[key] += 1
    else:
      pairs[key] = 1

print(len(pairs))
for pair in pairs:
  print(f"{pairs[pair]} : {pair}")