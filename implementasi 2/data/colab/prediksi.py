from tensorflow.keras import backend as K
from tensorflow.keras.models import load_model
import ast
import pandas as pd
import numpy as np
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inisialisasi model dengan error handling
modelCNN = None
modelCNNNon = None
modelGRU = None
modelGRUNon = None
modelLSTM = None
modelLSTMNon = None

best_thresholds_CNN = {}
best_thresholds_NonCNN = {}
best_thresholds_GRU = {}
best_thresholds_NonGRU = {}
best_thresholds_LSTM = {}
best_thresholds_NonLSTM = {}

try:
    # Load thresholds
    with open('data/mentahan/CNN/best_thresholds_CNN_sem.txt', 'r') as file:
        file_contents_CNN = file.read()
    with open('data/mentahan/CNN/best_thresholds_CNN_non.txt', 'r') as file:
        file_contents_NonCNN = file.read()

    with open('data/mentahan/BIGRU/best_thresholds_GRU_sem.txt', 'r') as file:
        file_contents_GRU = file.read()
    with open('data/mentahan/BIGRU/best_thresholds_GRU_non.txt', 'r') as file:
        file_contents_NonGRU = file.read()

    with open('data/mentahan/LSTM/best_thresholds_LSTM_sem.txt', 'r') as file:
        file_contents_LSTM = file.read()
    with open('data/mentahan/LSTM/best_thresholds_LSTM_non.txt', 'r') as file:
        file_contents_NonLSTM = file.read()

    best_thresholds_CNN = ast.literal_eval(file_contents_CNN)
    best_thresholds_NonCNN = ast.literal_eval(file_contents_NonCNN)
    best_thresholds_GRU = ast.literal_eval(file_contents_GRU)
    best_thresholds_NonGRU = ast.literal_eval(file_contents_NonGRU)
    best_thresholds_LSTM = ast.literal_eval(file_contents_LSTM)
    best_thresholds_NonLSTM = ast.literal_eval(file_contents_NonLSTM)
    
    logger.info("Thresholds loaded successfully")
except Exception as e:
    logger.error(f"Error loading thresholds: {e}")
    # Set default thresholds
    best_thresholds_CNN = {5: 0.5, 6: 0.5, 7: 0.5, 8: 0.5}
    best_thresholds_NonCNN = {5: 0.5, 6: 0.5, 7: 0.5, 8: 0.5}
    best_thresholds_GRU = {5: 0.5, 6: 0.5, 7: 0.5, 8: 0.5}
    best_thresholds_NonGRU = {5: 0.5, 6: 0.5, 7: 0.5, 8: 0.5}
    best_thresholds_LSTM = {5: 0.5, 6: 0.5, 7: 0.5, 8: 0.5}
    best_thresholds_NonLSTM = {5: 0.5, 6: 0.5, 7: 0.5, 8: 0.5}

try:
    logger.info("Loading CNN models...")
    modelCNN = load_model('model/CNN/CNN_model_semantic_indobert_tweet history_20 batch_16 learning_0.001.h5', custom_objects={"K": K})
    modelCNNNon = load_model('model/CNN/CNN_model_nonsemantic_indobert_tweet history_20 batch_16 learning_0.001.h5', custom_objects={"K": K})
    logger.info("CNN models loaded successfully")
except Exception as e:
    logger.error(f"Error loading CNN models: {e}")

try:
    logger.info("Loading GRU models...")
    modelGRU = load_model('model/GRU/BiGRU_model_semantic_indobert_tweet history_20 batch_16 learning_0.001.h5', custom_objects={"K": K})
    modelGRUNon = load_model('model/GRU/BiGRU_model_nonsemantic_indobert_tweet history_20 batch_16 learning_0.001.h5', custom_objects={"K": K})
    logger.info("GRU models loaded successfully")
except Exception as e:
    logger.error(f"Error loading GRU models: {e}")

try:
    logger.info("Loading LSTM models...")
    modelLSTM = load_model('model/LSTM/BiLSTM_model_semantic_indobert_tweet history_20 batch_16 learning_0.001.h5', custom_objects={"K": K})
    modelLSTMNon = load_model('model/LSTM/BiLSTM_model_nonsemantic_indobert_tweet history_20 batch_16 learning_0.001.h5', custom_objects={"K": K})
    logger.info("LSTM models loaded successfully")
except Exception as e:
    logger.error(f"Error loading LSTM models: {e}")

def change_char_at_index(string, index, new_char):
    if index < 0 or index >= len(string):
        return string
    else:
        new_string = string[:index] + new_char + string[index+1:]
        return new_string

def dummy_prediction():
    """Return dummy prediction untuk testing"""
    predictions = "1000000000000"
    yPredProb_values = np.array([[0.9, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]])
    return [predictions], yPredProb_values

# Prediksi
def prediksi(tweet, modelName, perluasan):
    try:
        # Pilih Model
        if modelName == "CNN":
            if perluasan == "0":
                if modelCNNNon is None:
                    logger.warning("CNN Non model not available, using dummy prediction")
                    return dummy_prediction()
                prediksi_result = modelCNNNon.predict(tweet)
                best_thresholds = best_thresholds_NonCNN
            else:
                if modelCNN is None:
                    logger.warning("CNN model not available, using dummy prediction")
                    return dummy_prediction()
                prediksi_result = modelCNN.predict(tweet)
                best_thresholds = best_thresholds_CNN
        elif modelName == "BIGRU":
            if perluasan == "0":
                if modelGRUNon is None:
                    logger.warning("GRU Non model not available, using dummy prediction")
                    return dummy_prediction()
                prediksi_result = modelGRUNon.predict(tweet)
                best_thresholds = best_thresholds_NonGRU
            else:
                if modelGRU is None:
                    logger.warning("GRU model not available, using dummy prediction")
                    return dummy_prediction()
                prediksi_result = modelGRU.predict(tweet)
                best_thresholds = best_thresholds_GRU
        else:  # LSTM
            if perluasan == "0":
                if modelLSTMNon is None:
                    logger.warning("LSTM Non model not available, using dummy prediction")
                    return dummy_prediction()
                prediksi_result = modelLSTMNon.predict(tweet)
                best_thresholds = best_thresholds_NonLSTM
            else:
                if modelLSTM is None:
                    logger.warning("LSTM model not available, using dummy prediction")
                    return dummy_prediction()
                prediksi_result = modelLSTM.predict(tweet)
                best_thresholds = best_thresholds_LSTM

        # Convert
        predHS = prediksi_result[0]
        predAbusive = prediksi_result[1]
        predGrup = prediksi_result[2]
        predGenre = prediksi_result[3]
        predStrong = prediksi_result[4]

        # Convert to Pandas
        yPredProb = pd.DataFrame({
            'Non_HS': predHS[:, 0], 'HS': predHS[:, 1], 'Abusive': predAbusive[:, 0], 
            'HS_Individual': predGrup[:, 0], 'HS_Group': predGrup[:, 1], 
            'HS_Religion': predGenre[:, 0], 'HS_Race': predGenre[:, 1],
            'HS_Physical': predGenre[:, 2], 'HS_Gender': predGenre[:, 3], 'HS_Other': predGenre[:, 4],
            'HS_Weak': predStrong[:, 0], 'HS_Moderate': predStrong[:, 1], 'HS_Strong': predStrong[:, 2]})
            
        yPredTest = yPredProb.values

        predictions = ""
        for i in range(len(yPredTest)):
            class_predictions = ""

            # HS/Non HS
            HSTrue = yPredTest[i, 0] > yPredTest[i, 1]
            if HSTrue:
                class_predictions += "1"
                class_predictions += "0"
            else:
                class_predictions += "0"
                class_predictions += "1"
            
            # Abusive
            if yPredTest[i, 2] > 0.5:
                class_predictions += "1" 
            else:
                class_predictions += "0"

            # Grup
            if class_predictions[0] == '0':
                HSGrup = yPredTest[i, 3] > yPredTest[i, 4]
                if HSGrup:
                    class_predictions += "1"
                    class_predictions += "0"
                else:
                    class_predictions += "0"
                    class_predictions += "1"
            else:
                class_predictions += "0"
                class_predictions += "0"

            # Loop Setiap Kelas Kategori
            gabunganKategori = 0
            if class_predictions[0] == '0':
                for j in range(5, 9):
                    gabunganKategori += yPredTest[i, j]
            
                if yPredTest[i, 9] > gabunganKategori:
                    class_predictions += "0"
                    class_predictions += "0"
                    class_predictions += "0"
                    class_predictions += "0"
                    class_predictions += "1"
                else:
                    # Tentukan kelas prediksi berdasarkan threshold terbaik
                    for j in range(5, 9):
                        if yPredTest[i, j] > best_thresholds.get(j, 0.5):
                            class_predictions += "1"  # Kelas positif
                        else:
                            class_predictions += "0"  # Kelas negatif
                    class_predictions += "0"
            else:
                class_predictions += "0"
                class_predictions += "0"
                class_predictions += "0"
                class_predictions += "0"
                class_predictions += "0"

            # Level
            if class_predictions[0] == '0':
                lastColumns = yPredTest[i, -3:]
                maxIndex = np.argmax(lastColumns) + 10
                if maxIndex == 10:
                    class_predictions += "1"
                    class_predictions += "0"
                    class_predictions += "0"
                elif maxIndex == 11:
                    class_predictions += "0"
                    class_predictions += "1"
                    class_predictions += "0"
                else:
                    class_predictions += "0"
                    class_predictions += "0"
                    class_predictions += "1"
            else:
                class_predictions += "0"
                class_predictions += "0"
                class_predictions += "0"

            # Tambahkan prediksi kelas untuk data baru
            predictions += class_predictions

        # Mengembalikan Semua HS ke 0 Jika non hs 1
        if predictions[0] == "1":
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

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return dummy_prediction()