# test_prediction.py
from data.colab.prediksi import prediksi
from data.colab.dataCleaning import casefolding, hapusKata, normalizeText
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

factory = StemmerFactory()
stemmer = factory.create_stemmer()

def test_prediction(text):
    print(f"\n=== PREDICTION TEST: '{text}' ===")
    
    # Preprocessing
    tweet = casefolding(text)
    tweet = hapusKata(tweet) 
    tweet = normalizeText(tweet)
    tweet = stemmer.stem(tweet)
    
    print("After preprocessing:", tweet)
    
    # Prediction
    result = prediksi(tweet, "CNN", "1")
    print("Prediction result:", result)
    
    return result

# Test dengan kata yang sama
test_prediction("babi")
test_prediction("anjing") 
test_prediction("kontol")