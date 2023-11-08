import re
from functools import wraps

from flask import request, jsonify

from transformers import BertTokenizer, BertModel, XLNetTokenizer, XLNetModel


# Load pre-trained BERT tokenizer and model
tokenizer = BertTokenizer.from_pretrained('bert-base-cased')
model = BertModel.from_pretrained('bert-base-cased')

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def is_valid_apikey(provided_key):
    return True


def require_apikey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        provided_key = request.headers.get('x-api-key')
        if provided_key and is_valid_apikey(provided_key):
            return view_function(*args, **kwargs)
        else:
            return jsonify({"error": "API key is missing or incorrect"}), 401
    return decorated_function


def get_vector_bert(text):
    text = preprocess_text(text)

    # Encode text_task1
    inputs = tokenizer(text, return_tensors="pt")
    outputs = model(**inputs)

    # Only take the embeddings of the [CLS] token (the first token)
    vector = outputs.last_hidden_state[:, 0, :].detach().numpy()
    print(len(vector[0]))
    return vector[0]


def get_index_mapping():
    return {
        "settings": {
            "number_of_shards": 2,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "vector": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": "true",
                    "similarity": "cosine"
                },
                "original_text": {
                    "type": "text"
                }
            }
        }
    }


def get_search_query(query_vector, k, min_score):
    return {
        "knn": {
            "field": "vector",
            "query_vector": query_vector,
            "k": k,
            "num_candidates": 10,
        },
        "min_score": min_score,
        "_source": False
    }