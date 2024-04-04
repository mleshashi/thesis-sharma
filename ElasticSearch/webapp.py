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

@app.route('/')
def index():
    # Render the main page
    return render_template('index.html')

@app.route('/get-random-topic', methods=['GET'])
def get_random_topic():
    random_topic = random.choice(topics_df['Topic'].to_list())
    return jsonify({"topic": random_topic})

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

if __name__ == '__main__':
    app.run(debug=True)