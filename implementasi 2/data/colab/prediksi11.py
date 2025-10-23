from keras import backend as K
from tensorflow.keras.models import load_model
import ast
import pandas as pd
import numpy as np

with open('data/mentahan/CNN/best_thresholds_CNN_sem.txt', 'r') as file:
  # Read the contents of the file
  file_contents_CNN = file.read()
with open('data/mentahan/CNN/best_thresholds_CNN_non.txt', 'r') as file:
  # Read the contents of the file
  file_contents_NonCNN = file.read()

with open('data/mentahan/BIGRU/best_thresholds_GRU_sem.txt', 'r') as file:
  # Read the contents of the file
  file_contents_GRU = file.read()
with open('data/mentahan/BIGRU/best_thresholds_GRU_non.txt', 'r') as file:
  # Read the contents of the file
  file_contents_NonGRU = file.read()

with open('data/mentahan/LSTM/best_thresholds_LSTM_sem.txt', 'r') as file:
  # Read the contents of the file
  file_contents_LSTM = file.read()
with open('data/mentahan/LSTM/best_thresholds_LSTM_non.txt', 'r') as file:
  # Read the contents of the file
  file_contents_NonLSTM = file.read()

best_thresholds_CNN = ast.literal_eval(file_contents_CNN)
best_thresholds_NonCNN = ast.literal_eval(file_contents_NonCNN)

best_thresholds_GRU = ast.literal_eval(file_contents_GRU)
best_thresholds_NonGRU = ast.literal_eval(file_contents_NonGRU)

best_thresholds_LSTM = ast.literal_eval(file_contents_LSTM)
best_thresholds_NonLSTM = ast.literal_eval(file_contents_NonLSTM)


modelCNN = load_model('model/CNN/CNN_model_nonsemantic_indobert_tweet history_20 batch_16 learning_0.001.h5', custom_objects={"K": K})
modelCNNNon = load_model('model/CNN/CNN_model_nonsemantic_indobert_tweet history_20 batch_16 learning_0.001.h5', custom_objects={"K": K})

modelGRU = load_model('model/GRU/BiGRU_model_semantic_indobert_tweet history_20 batch_16 learning_0.001.h5', custom_objects={"K": K})
modelGRUNon = load_model('model/GRU/BiGRU_model_nonsemantic_indobert_tweet history_20 batch_16 learning_0.001.h5', custom_objects={"K": K})

modelLSTM = load_model('model/LSTM/BiLSTM_model_semantic_indobert_tweet history_20 batch_16 learning_0.001.h5', custom_objects={"K": K})
modelLSTMNon = load_model('model/LSTM/BiLSTM_model_nonsemantic_indobert_tweet history_20 batch_16 learning_0.001.h5', custom_objects={"K": K})


def change_char_at_index(string, index, new_char):
  if index < 0 or index >= len(string):
    # Index is out of range
    return string
  else:
    new_string = string[:index] + new_char + string[index+1:]
    return new_string

# Prediksi
def prediksi(tweet, modelName, perluasan):

  # Pilih Model
  if modelName=="CNN":
    if perluasan=="0":
      prediksi = modelCNNNon.predict(tweet)
      best_thresholds = best_thresholds_NonCNN
    else:
      prediksi = modelCNN.predict(tweet)
      best_thresholds = best_thresholds_CNN
  elif modelName=="BIGRU":
    if perluasan == "0":
      prediksi = modelGRUNon.predict(tweet)
      best_thresholds = best_thresholds_NonGRU
    else:
      prediksi = modelGRU.predict(tweet)
      best_thresholds = best_thresholds_GRU
  else:
    if perluasan == "0":
      prediksi = modelLSTMNon.predict(tweet)
      best_thresholds = best_thresholds_NonLSTM
    else:
      prediksi = modelLSTM.predict(tweet)
      best_thresholds = best_thresholds_LSTM

  # Convert
  predHS = prediksi[0]
  predAbusive = prediksi[1]
  predGrup = prediksi[2]
  predGenre = prediksi[3]
  predStrong = prediksi[4]

  # Convert to Pandas
  yPredProb = pd.DataFrame({
    'Non_HS': predHS[:, 0], 'HS': predHS[:, 1], 'Abusive': predAbusive[:, 0], 
    'HS_Individual': predGrup[:, 0], 'HS_Group': predGrup[:, 1], 
    'HS_Religion': predGenre[:, 0], 'HS_Race': predGenre[:, 1],
    'HS_Physical': predGenre[:, 2], 'HS_Gender': predGenre[:, 3], 'HS_Other': predGenre[:, 4],
    'HS_Weak': predStrong[:, 0], 'HS_Moderate': predStrong[:, 1], 'HS_Strong': predStrong[:, 2]})
    
  yPredTest = yPredProb.values

  predictions=""
  for i in range(len(yPredTest)):
    class_predictions=""

    # HS/Non HS
    HSTrue = yPredTest[i, 0] > yPredTest[i, 1]
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
      HSGrup = yPredTest[i, 3] > yPredTest[i, 4]
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
    gabunganKategori = 0
    if class_predictions[0]=='0':
      for j in range(5, 9):
        gabunganKategori += yPredTest[i, j]
    
      if yPredTest[i, 9] > gabunganKategori:
        class_predictions+="0"
        class_predictions+="0"
        class_predictions+="0"
        class_predictions+="0"
        class_predictions+="1"
      else:
      # Tentukan kelas prediksi berdasarkan threshold terbaik
        for j in range(5, 9):
          if yPredTest[i, j] > best_thresholds[j]:
            class_predictions+="1"  # Kelas positif
          else:
            class_predictions+="0"  # Kelas negatif
        class_predictions+="0"
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

  # Mengembalikan Semua HS ke 0 Jika non hs 1
  if predictions[0][0] == "1":
    yPredProb.at[0, "HS_Individual"] = 0
    yPredProb.at[0, "HS_Group"] = 0
    yPredProb.at[0, "HS_Religion"] = 0
    yPredProb.at[0, "HS_Race"] = 0
    yPredProb.at[0, "HS_Physical"] = 0
    yPredProb.at[0, "HS_Gender"] = 0
    yPredProb.at[0, "HS_Other"] = 0
    yPredProb.at[0, "HS_Weak"] = 0
    yPredProb.at[0, "HS_Moderate"] = 0
    yPredProb.at[0, "HS_Strong"] = 0

  nilaiKembali = []
  nilaiKembali.append(predictions)
  nilaiKembali.append(yPredProb.values)
  return nilaiKembali
