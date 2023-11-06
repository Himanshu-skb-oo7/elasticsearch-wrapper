import os
from ast import literal_eval

from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import utils

application= app = Flask(__name__)

ES_ENDPOINT = os.getenv('ES_ENDPOINT')
API_KEY = os.getenv('API_KEY')
ES_CLIENT = Elasticsearch(ES_ENDPOINT, api_key=API_KEY)

@app.route('/')
def test():
    return 'SERVER IS UP AND RUNNING!'


@app.route('/index', methods=['POST', 'DELETE'])
@utils.require_apikey
def index():
    index = request.form.get('index')
    if not index:
        return jsonify(status='error', message='Missing parameter: index'), 400
    
    try:
        if request.method == 'POST':
            mapping = utils.get_index_mapping()
            ES_CLIENT.indices.create(index=index, body=mapping)
            return jsonify(status='success', message=f"Index '{index}' created successfully"), 200
        
        if request.method == 'DELETE':
            ES_CLIENT.indices.delete(index=index)
            return jsonify(status='success', message=f"Index '{index}' deleted successfully"), 200
    except Exception as e:
        return jsonify(status='error', message=e.message), e.status_code


@app.route('/item', methods=['POST', 'DELETE'])
@utils.require_apikey
def insert_item():
    if request.method == "POST":
        text = request.form.get('text')
        index = request.form.get('index')
        item_id = request.form.get('id')

        if not (text and index and item_id):
            return jsonify(status='error', message='Missing parameter(s): text, index, or id'), 400

        try:
            vector = utils.get_vector_bert(text)
            doc = {"vector": vector}
            ES_CLIENT.index(index=index, id=item_id, body=doc)
            return jsonify(status='success', message=f"Item has been inserted successfully"), 200
        except Exception as e:
            return jsonify(status='error', message=e.message), e.status_code

    if request.method == "DELETE":
        index = request.form.get('index')
        item_id = request.form.get('id')

        if not (index and item_id):
            return jsonify(status='error', message='Missing parameter(s): index or id'), 400

        try:
            ES_CLIENT.delete(index=index, id=item_id)
            return jsonify(status='success', message=f'Item {item_id} deleted successfully from Index {index}'), 200
        except Exception as e:
            return jsonify(status='error', message=e.message), e.status_code


@app.route('/bulk-insert', methods=['POST'])
@utils.require_apikey
def bulk_insert():
    index = request.form.get('index')
    items = request.form.get('items')

    if not (items and index):
        return jsonify(status='error', message='Missing parameter(s): items or index'), 400

    items = literal_eval(items)

    try:
        for item in items:
            try:
                item_id = item['id']
                vector = utils.get_vector_bert(item['text'])
                doc = {"vector": vector}
                ES_CLIENT.index(index=index, id=item_id, body=doc)
            except Exception as e:
                pass

        return jsonify(status='success', message=f"Items bulk inserted successfully"), 200
    except Exception as e:
        return jsonify(status='error', message=e.message), e.status_code


@app.route('/search', methods=['POST'])
@utils.require_apikey
def search():
    try:
        text = request.form.get('text')
        index = request.form.get('index')
        query_vector = utils.get_vector_bert(text)
        search_query = utils.get_search_query(query_vector)

        response = ES_CLIENT.search(index=index, body=search_query)
        return jsonify(status='success', result=response.get('hits', [])), 200
    except Exception as e:
        return jsonify(status='error', message=e.message), e.status_code



if __name__ == '__main__':
    app.run()
