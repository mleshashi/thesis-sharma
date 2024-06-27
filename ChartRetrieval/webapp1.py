# app.py
from flask import Flask, request, jsonify, render_template
from elasticsearch import Elasticsearch
import pandas as pd
import random
import torch
import torch.nn.functional as F
from torch import Tensor
from loadModel import load_model, load_tokenizer
from getEmbeddings import get_detailed_instruct, embed_texts

app = Flask(__name__)
es = Elasticsearch(["http://localhost:9200"])
index_name = "documents"

# Load models
model_name_1 = 'intfloat/e5-mistral-7b-instruct'
#model_name_2 = 'Alibaba-NLP/gte-Qwen2-7B-instruct'
#model_name_3 = 'another-model-name-1'
#model_name_4 = 'another-model-name-2'

device = 'cuda' if torch.cuda.is_available() else 'cpu'

tokenizer_1 = load_tokenizer(model_name_1)
model_1 = load_model(model_name_1)
#tokenizer_2 = load_tokenizer(model_name_2, trust_remote_code=True)
#model_2 = load_model(model_name_2, trust_remote_code=True)
#tokenizer_3 = load_tokenizer(model_name_3)
#model_3 = load_model(model_name_3)
#tokenizer_4 = load_tokenizer(model_name_4)
#model_4 = load_model(model_name_4)

# Load topics DataFrame globally
topics_df = pd.read_csv('../dataset/TopRelevant_topics1.csv')
Manualtopics_df = pd.read_csv('../dataset/manual_topics.csv')

@app.route('/')
def index():
    # Render the main page
    return render_template('index1.html')

@app.route('/get-topics', methods=['GET'])
def get_topics():
    topics_list = topics_df['Topic'].tolist()
    return jsonify({"topics": topics_list})

@app.route('/get-manual-topics', methods=['GET'])
def get_manual_topics():
    manual_topics_list = Manualtopics_df['Topic'].tolist()
    return jsonify({"topics": manual_topics_list})

@app.route('/search', methods=['POST'])
def search():
    topic = request.json['topic']
    task = 'Given a web search query, retrieve relevant passages that answer the query'
    query = get_detailed_instruct(task, topic)
    
    # Get embeddings for all models
    topic_embedding_1 = embed_texts(query, tokenizer_1, model_1, device)
    topic_embedding_2 = embed_texts(query, tokenizer_1, model_1, device)
    topic_embedding_3 = embed_texts(query, tokenizer_1, model_1, device)
    topic_embedding_4 = embed_texts(query, tokenizer_1, model_1, device)

    # Elasticsearch query for the first model
    script_query_1 = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'mistral_embedding') + 1.0",
                "params": {"query_vector": topic_embedding_1}
            }
        }
    }

    # Elasticsearch query for the second model
    script_query_2 = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'mistral_embedding') + 1.0",
                "params": {"query_vector": topic_embedding_2}
            }
        }
    }

    # Elasticsearch query for the third model
    script_query_3 = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'mistral_embedding') + 1.0",
                "params": {"query_vector": topic_embedding_3}
            }
        }
    }

    # Elasticsearch query for the fourth model
    script_query_4 = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'mistral_embedding') + 1.0",
                "params": {"query_vector": topic_embedding_4}
            }
        }
    }

    # Get results for the first model
    response_1 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_1,
        "_source": ["title", "content","image_data"]
    })

    # Get results for the second model
    response_2 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_2,
        "_source": ["title", "content","image_data"]
    })

    # Get results for the third model
    response_3 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_3,
        "_source": ["title", "content","image_data"]
    })

    # Get results for the fourth model
    response_4 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_4,
        "_source": ["title", "content","image_data"]
    })

    documents_1 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"], "image_data": hit["_source"]["image_data"]} for hit in response_1['hits']['hits']]
    documents_2 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"], "image_data": hit["_source"]["image_data"]} for hit in response_2['hits']['hits']]
    documents_3 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"], "image_data": hit["_source"]["image_data"]} for hit in response_3['hits']['hits']]
    documents_4 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"], "image_data": hit["_source"]["image_data"]} for hit in response_3['hits']['hits']]
    
    return jsonify({
        "model_1_documents": documents_1,
        "model_2_documents": documents_2,
        "model_3_documents": documents_3,
        "model_4_documents": documents_4
    })

@app.route('/get-random-image', methods=['GET'])
def get_random_image():
    index_name = "documents"
    total_docs = es.count(index=index_name)['count']

    # Cap the max_offset to avoid exceeding the max_result_window
    max_offset = min(total_docs, 10000) - 1
    random_offset = random.randint(0, max_offset)

    # Fetch one document at a random offset
    response = es.search(index=index_name, body={
        "size": 1,
        "query": {"match_all": {}},
        "from": random_offset,
        "_source": ["image_data"]  # Only request the image data field
    })
    
    if response['hits']['hits']:
        doc = response['hits']['hits'][0]['_source']
        return jsonify({"image_data": doc['image_data']})  # Ensure 'image_data' is the correct field name
    else:
        return jsonify({"error": "No documents found"}), 404

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
    #app.run(host='0.0.0.0', port=5000, debug=True)
