import torch, tqdm
import transformers as tfm
import numpy as np
from tensorflow.keras.preprocessing import sequence

model_class_indobert, tokenizer_class_indobert, pretrained_weights_indobert = (tfm.BertModel, tfm.BertTokenizer, 'indolem/indobertweet-base-uncased')
tokenizerIndobert = tokenizer_class_indobert.from_pretrained(pretrained_weights_indobert)
modelIndobert = model_class_indobert.from_pretrained(pretrained_weights_indobert)

def embed(tweet):
    tweet = tokenizerIndobert.encode(tweet, add_special_tokens=True)
    tweet = sequence.pad_sequences([tweet], maxlen=80, padding="post", truncating="post")

    return tweet


def paddedSensor(tweet):
    tweet = embed(tweet)

    train_ids = torch.tensor(np.array(tweet)).to(torch.int64)
    train_features_sem = []
    batch_size = 64
    for batch in tqdm.tqdm(range(0,len(train_ids),batch_size)):
        batch_ids = train_ids[batch:batch+batch_size]
        batch_attention_mask = (batch_ids != 0)
        with torch.no_grad():
            train_last_hidden_states = modelIndobert(batch_ids, attention_mask=batch_attention_mask)
            train_features_sem.append(train_last_hidden_states[0])

    train_features_sem = np.concatenate(train_features_sem)

    return train_features_sem