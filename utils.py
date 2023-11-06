from transformers import BertTokenizer, BertModel

def get_vector_bert(text):
    # Load pre-trained BERT tokenizer and model
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased')

    # Encode text_task1
    inputs = tokenizer(text, return_tensors="pt")
    outputs = model(**inputs)

    # Only take the embeddings of the [CLS] token (the first token)
    vector = outputs.last_hidden_state[:, 0, :].detach().numpy()
    return vector[0]

def get_index_mapping():
    return {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "vector": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": "true",
                    "similarity": "cosine"
                }
            }
        }
    }


def get_search_query(query_vector):
    return {
        "knn": {
            "field": "vector",
            "query_vector": query_vector,
            "k": 10,
            "num_candidates": 100,
        },
        "min_score": 0.8
    }