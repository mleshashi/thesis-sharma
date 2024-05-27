# app.py
from flask import Flask, request, jsonify, render_template
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import pandas as pd
import random

app = Flask(__name__)
es = Elasticsearch(["http://localhost:9200"])
model = SentenceTransformer("all-MiniLM-L6-v2")
index_name = "documents"

# Load topics DataFrame globally
topics_df = pd.read_csv('../dataset/TopRelevant_topics.csv')
Manualtopics_df = pd.read_csv('../dataset/manual_topics.csv')

@app.route('/')
def index():
    # Render the main page
    return render_template('index.html')

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
    topic_embedding = model.encode(topic).tolist()

    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                "params": {"query_vector": topic_embedding}
            }
        }
    }

    response = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query,
        "_source": ["title", "content"]
    })

    documents = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"]} for hit in response['hits']['hits']]
    return jsonify(documents)

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
    app.run(debug=True)