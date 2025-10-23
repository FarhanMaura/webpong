import nltk, re, copy, requests, json, torch
from nltk.tokenize import word_tokenize
import torch.nn.functional as F
from nltk.corpus import stopwords
from nltk.corpus import wordnet as wn
from data.colab.dataCleaning import casefolding
from transformers import AutoTokenizer, AutoModel

def kataKasar(word):
  kondisi = False
  with open(r'data/mentahan/kamus-kasar.txt', 'r') as kasar:
    kataKasar = [line.split(',') for line in kasar.read().splitlines()]
  if word.lower() in kataKasar[0]:
    kondisi = True
  
  return kondisi

def definisiKata(kata):
  synsets = wn.synsets(kata, lang='ind')
  if len(synsets) == 0:
    try:
      url = f"http://kateglo.lostfocus.org/api.php?format=json&phrase={kata}"
      response = requests.get(url)
      data = response.text
      parsed = json.loads(data)
      definisi = parsed["kateglo"]["definition"][0]['def_text']
      return definisi
    except:
      return kata
  else:
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=id&dt=t&q={synsets[0].definition()}"
    translation = requests.get(url)

    kalimat = translation.json()[0][0][0]
    # casefolding
    kalimat = casefolding(kalimat)
    
    return kalimat

def sinonimKateglo(kata):
  url = f"http://kateglo.lostfocus.org/api.php?format=json&phrase={kata}"
  response = requests.get(url)
  data = response.text
  parsed = json.loads(data)
  post = parsed["kateglo"]["relation"]["s"]
  daftarKata = []
  for i in range(len(post)-1):
    daftarKata.append(post[f"{i}"]["related_phrase"])
  
  return daftarKata

model_name = 'indolem/indobertweet-base-uncased'
#model_name = 'indobenchmark/indobert-base-p2'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
def cekSimilarity(kata1, kata2):
    if kata1 == kata2:
      return 0
    # Tokenize the words and add special tokens
    inputs1 = tokenizer(kata1, return_tensors="pt")
    inputs2 = tokenizer(kata2, return_tensors="pt")

    # Generate the word embeddings
    with torch.no_grad():
      outputs1 = model(**inputs1)
      outputs2 = model(**inputs2)

    # Get the embeddings for the [CLS] token
    embeddings1 = outputs1.last_hidden_state[:, 0, :]
    embeddings2 = outputs2.last_hidden_state[:, 0, :]
    similarity = F.cosine_similarity(embeddings1, embeddings2)

    return similarity.item()

def kateglo_role(kata):
  # Kateglo untuk role
  url = f"http://kateglo.lostfocus.org/api.php?format=json&phrase={kata}"
  response = requests.get(url)
  data = response.text
  parsed = json.loads(data)
  role = parsed["kateglo"]["lex_class"]
  return role

def lesk(kata, kalimat):
  synsets = wn.synsets(kata, lang='ind')
  max_overlap = 0
  context = set(kalimat.split())
  
  for synset in synsets:
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=id&dt=t&q={synset.definition()}"
    translation = requests.get(url)

    kalimat = translation.json()[0][0][0]
    # casefolding
    kalimat = casefolding(kalimat)

    signature = set(kalimat.split())
    for example in synset.examples():
      # print(example)
      urlContoh = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=id&dt=t&q={example}"
      translationExamples = requests.get(urlContoh)
      contohKata = translationExamples.json()[0][0][0]

      # casefolding
      contohKata = casefolding(contohKata)
      
      signature.update(set(contohKata.split()))
    overlap = len(signature.intersection(context))
    if overlap > max_overlap:
      max_overlap = overlap
      best_sense = synset

  # Cek max overlap
  sinonim = []
  if max_overlap==0:
    for lemma in synsets[0].lemma_names(lang='ind'):
      sinonim.append(lemma)
  else:
    for lemma in best_sense.lemma_names(lang='ind'):
      sinonim.append(lemma)

  return sinonim

roleKata = ['n', 'v', 'adj', 'a']

def semanticExpantion(text):
  teksAsli = copy.copy(text)
  text = text.split()
  teksAnt=[]

  # Antonim
  for x in text:
    teksAnt.append(x)
  for y in range(0, len(teksAnt)):
    if(teksAnt[y]=="tidak"):
      try:

        # Get Kateglo
        url = "http://kateglo.lostfocus.org/api.php?format=json&phrase="+teksAnt[y+1]
        response = requests.get(url)
        data = response.text
        parsed = json.loads(data)

        # Cek Kalimat
        if(parsed['kateglo']['lex_class']=="adj"):
          post = parsed["kateglo"]["relation"]["a"]
          lenPost=len(post)
          for x in range(0,lenPost):
            st=str(x)
            value=post[st]
            if(value['rel_type']=='a' and value['lex_class']=='adj'):
              ant=value['related_phrase']
              teksAnt[y]=ant
              teksAnt[y+1]=""
              break

      except:
        print("ERROR")


  # Sinonim
  teksSin = []
  textJoin = " ".join(teksAnt)
  text = textJoin.split()

  for x in text:
    teksSin.append(x)

  # Jika Kata Kurang Panjang
  if len(teksSin) <= 3:
    teksBaru = []
    for y in range(0, len(teksSin)):
      teksBaru.append(teksSin[y])

      definisi = definisiKata(teksSin[y])
      definisiSplit = definisi.split()
      for x in definisiSplit:
        teksBaru.append(x)
    teksSin = []
    teksSin = copy.copy(teksBaru)

  detailDaftarSinonim = {}
  listCekKata = []

  for y in range(0, len(teksSin)):
    try:
      jenisKata = wn.synsets(teksSin[y], lang="ind")
      kondisiKasar = kataKasar(teksSin[y])
      if jenisKata[0].pos() in roleKata or kondisiKasar:
        try:
          listCekKata.append(y)

          role = kateglo_role(teksSin[y])
          daftarAllSinonimNew = lesk(teksSin[y], textJoin)
          daftarSinonim = []
          daftarAllSinonim = [daftarSinonim for daftarSinonim in daftarAllSinonimNew if daftarSinonim != teksSin[y]]

          # Cek Jenis Sinonim
          daftarKataRelevan = {}
          daftarNilai = {}
          if len(daftarAllSinonim) <= 1:
            daftarAllSinonim.extend(sinonimKateglo(teksSin[y]))
            
          for x in range(0, len(daftarAllSinonim)):
            kata = daftarAllSinonim[x].replace('_', ' ')
            kata = casefolding(kata)

            nilai = cekSimilarity(teksSin[y], kata)
            daftarNilai[x] = nilai
            daftarKataRelevan[x] = kata
          
          # Sorted Nilai
          sortedNilai = sorted(daftarNilai.items(), key=lambda x: x[1], reverse=True)
          if len(sortedNilai)<2:
            highestKey = [item[0] for item in sortedNilai[:1]]
          else:
            highestKey = [item[0] for item in sortedNilai[:2]]
          for i in highestKey:
            daftarSinonim.append(daftarKataRelevan[i])

          if len(daftarSinonim) < 2:
            detailDaftarSinonim[y] = daftarSinonim[0]
          else:
            detailDaftarSinonim[y] = daftarSinonim[0] + " " + daftarSinonim[1]

        except:
          pass

    except:
      pass

  addNew = copy.copy(teksSin)
  for key in reversed(detailDaftarSinonim):
    try:
      addNew.insert(key+1, detailDaftarSinonim[key])
    except:
      addNew.append(detailDaftarSinonim[value])
  text = " ".join(addNew)

  return text