from keras import backend as K
from tensorflow.keras.models import load_model
import ast
import pandas as pd
import numpy as np

with open('data/mentahan/CNN/best_thresholds_SemCNN_NewRole.txt', 'r') as file:
  # Read the contents of the file
  file_contents = file.read()

best_thresholds = ast.literal_eval(file_contents)

model = load_model('model/CNN/CNN_model_semantic_indobert_tweet history_20 batch_16 learning_0.001.h5', custom_objects={"K": K})

def change_char_at_index(string, index, new_char):
  if index < 0 or index >= len(string):
    # Index is out of range
    return string
  else:
    new_string = string[:index] + new_char + string[index+1:]
    return new_string

# Prediksi
def prediksi(tweet):

  # Prediksi
  prediksi = model.predict(tweet)

  # Convert
  predHS = prediksi[0]
  predAbusive = prediksi[1]
  predKelompok = prediksi[2]
  predGenre = prediksi[3]
  predStrong = prediksi[4]

  # Convert to Pandas
  yPredProb = pd.DataFrame({
    'Non_HS': predHS[:, 0], 'HS': predHS[:, 1], 
    'Abusive': predAbusive[:, 0], 
    'HS_Individual': predKelompok[:, 0], 'HS_Group': predKelompok[:, 1], 
    'HS_Religion': predGenre[:, 0], 'HS_Race': predGenre[:, 1],
    'HS_Physical': predGenre[:, 2], 'HS_Gender': predGenre[:, 3], 'HS_Other': predGenre[:, 4],
    'HS_Weak': predStrong[:, 0], 'HS_Moderate': predStrong[:, 1], 'HS_Strong': predStrong[:, 2]})
    
  yPredTest = yPredProb.values

  predictions=""
  for i in range(len(yPredTest)):
    class_predictions=""

    # HS/Non HS
    HSTrue = yPredTest[i, 0] > 0.5
    if HSTrue:
      class_predictions+="1"
      class_predictions+="0"
    else:
      class_predictions+="0"
      class_predictions+="1"
    
    # Abusive
    if yPredTest[i, 2] > 0.5:
      class_predictions+="1" 
    else:
      class_predictions+="0"

    # Grup
    if class_predictions[0]=='0':
      HSGrup = yPredTest[i, 3] > 0.5
      if HSGrup:
        class_predictions+="1"
        class_predictions+="0"
      else:
        class_predictions+="0"
        class_predictions+="1"
    else:
      class_predictions+="0"
      class_predictions+="0"

    # Loop Setiap Kelas Kategori
    if class_predictions[0]=='0':
      for j in range(5, 10):
        # Tentukan kelas prediksi berdasarkan threshold terbaik
        if yPredTest[i, j] > best_thresholds[j]:
          class_predictions+="1"  # Kelas positif
        else:
          class_predictions+="0"  # Kelas negatif
    else:
      class_predictions+="0"
      class_predictions+="0"
      class_predictions+="0"
      class_predictions+="0"
      class_predictions+="0"

    # Level
    if class_predictions[0]=='0':
      lastColumns = yPredTest[i, -3:]
      maxIndex = np.argmax(lastColumns)+10
      if maxIndex==10:
        class_predictions+="1"
        class_predictions+="0"
        class_predictions+="0"
      elif maxIndex==11:
        class_predictions+="0"
        class_predictions+="1"
        class_predictions+="0"
      else:
        class_predictions+="0"
        class_predictions+="0"
        class_predictions+="1"
    else:
      class_predictions+="0"
      class_predictions+="0"
      class_predictions+="0"

    # Tambahkan prediksi kelas untuk data baru
    predictions+=class_predictions

  nilaiKembali = []
  nilaiKembali.append(predictions)
  nilaiKembali.append(yPredProb.values)
  return nilaiKembali