import pandas as pd
import re

#casefolding
def casefolding(text):
  text = text.lower()
  url_pattern_https = re.compile(r'https?://\S+')
  url_pattern_http = re.compile(r'https://\S+')
  text = url_pattern_https.sub('', text)
  text = url_pattern_http.sub('', text)
  # text = re.sub(r'\d+','', text)
  text = re.sub(r"[!@#$%^&*)(-_=+;,./{}|:<>?\"ù÷ù÷ù÷]'.,",'',text)
  text = re.sub(r"&amp", "", text)
  text = re.sub(r"\n", "", text)
  # text = re.sub(r":(", "", text)
  text = re.sub(r"amp", "", text)
  text = re.sub(r"\\", "", text)
  text = re.sub(r"=", "", text)
  text = re.sub(r"|", "", text)
  text = re.sub(r"»", "", text)
  text = re.sub(r"&gt", "", text)
  text = re.sub(r"&", "dan", text)
  text = re.sub(r'#\w+', '', text)
  text = re.sub(r"&lt", "", text)
  text = re.sub(r"xf", "", text)
  text = re.sub(r";", "", text)
  text = re.sub(r"ð??", "", text)
  text = re.sub(r"¦", "", text)
  text = re.sub(r"_", "", text)
  text = re.sub(r"xa", "", text)
  text = re.sub(r"\n", "", text)
  text = re.sub(r"xa", "", text)
  text = re.sub(r"xx", "", text)
  text = re.sub(r"xa", "", text)
  text = re.sub(r'"', '', text)
  text = re.sub(r"'", "", text)
  text = re.sub(r"xc", "", text)
  #text = text.replace("-", " ")
  text = text.replace("  ", " ")
  text = text.replace(".", "")
  text = text.replace(",", "")
  text = text.replace("?", " ")
  text = text.strip()
  return text

def hapusKata(text):
  hapusKata = ["user", "rt", "user:"]
  text = " ".join([word for word in text.split() if word not in hapusKata])
  return text

# Slang Word
def normalizeText(text):
  kamus_normal = pd.read_csv("data/mentahan/kamusnormalisasi.csv", encoding='latin-1', header=None, names=["non-standard word","standard word"])
  kamus_normal = kamus_normal.iloc[::-1]
  nonstdword = kamus_normal['non-standard word'].values.tolist()
  stdword = kamus_normal['standard word'].values.tolist()
  text = text.split(" ")
  for i in range(len(text)):
    if text[i] in nonstdword:
      index = nonstdword.index(text[i])
      text[i] = stdword[index]
  return ' '.join(map(str, text))