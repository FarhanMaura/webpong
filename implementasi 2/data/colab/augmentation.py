import requests

def backTranslate(text, target_language='en', source_language='auto'):
  url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_language}&tl={target_language}&dt=t&q={text}"
  response = requests.get(url)
  translation = response.json()[0]
  bahasa = ""
  try:
    for i in translation:
      bahasa += i[0]
  except:
    pass
  return bahasa