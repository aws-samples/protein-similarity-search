import gc
import re
import torch
import numpy

from transformers import T5EncoderModel, T5Tokenizer

def model_fn(model_dir):
    # Load model
    tokenizer = T5Tokenizer.from_pretrained(model_dir, do_lower_case=False)
    model = T5EncoderModel.from_pretrained(model_dir)

    gc.collect()
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    model = model.eval()

    return model, tokenizer

def predict_fn(data, model_and_tokenizer):
    model, tokenizer = model_and_tokenizer
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    
    # Tokenize sentences
    sequences = data.pop("inputs", data)
    sequences = [re.sub(r"[UZOB]", "X", sequence) for sequence in sequences]
    
    ids = tokenizer.batch_encode_plus(sequences, add_special_tokens=True, padding=True)
    
    # converts ids and attention mask into pytorch format
    input_ids = torch.tensor(ids['input_ids']).to(device)
    attention_mask = torch.tensor(ids['attention_mask']).to(device)

    # embeddings generation
    with torch.no_grad():
        embedding = model(input_ids=input_ids,attention_mask=attention_mask)
    
    embedding = embedding.last_hidden_state.cpu().numpy()
    
    #features extraction
    features = [] 
    for seq_num in range(len(embedding)):
        seq_len = (attention_mask[seq_num] == 1).sum()
        seq_emd = embedding[seq_num][:seq_len-1]
        features.append(seq_emd)
    
    return {"features": features}
