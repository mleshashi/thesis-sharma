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
device = 'cuda' if torch.cuda.is_available() else 'cpu'
tokenizer_1 = load_tokenizer(model_name_1)
model_1 = load_model(model_name_1)
#tokenizer_2 = load_tokenizer(model_name_2, trust_remote_code=True)
#model_2 = load_model(model_name_2, trust_remote_code=True)

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
    
    # Get embeddings for both models
    topic_embedding_1 = embed_texts(query, tokenizer_1, model_1, device)
    topic_embedding_2 = embed_texts(query, tokenizer_1, model_1, device)

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

    # Get results for the first model
    response_1 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_1,
        "_source": ["title", "content"]
    })

    # Get results for the second model
    response_2 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_2,
        "_source": ["title", "content"]
    })

    documents_1 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"]} for hit in response_1['hits']['hits']]
    documents_2 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"]} for hit in response_2['hits']['hits']]
    
    return jsonify({"model_1_documents": documents_1, "model_2_documents": documents_2})

@app.route('/get-random-document', methods=['GET'])
def get_random_document():
    index_name = "documents"
    total_docs = es.count(index=index_name)['count']

    # Generate a random offset
    random_offset = random.randint(0, total_docs - 1)

    # Fetch one document at a random offset
    response = es.search(index=index_name, body={
        "size": 1,
        "query": {"match_all": {}},
        "from": random_offset
    })
    
    doc = response['hits']['hits'][0]['_source']
    return jsonify({"title": doc['title'], "content": doc['content']})    

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
