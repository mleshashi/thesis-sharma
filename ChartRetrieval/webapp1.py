from flask import Flask, request, jsonify, render_template
from elasticsearch import Elasticsearch
import pandas as pd
import random
import torch
from loadModel import load_model, load_tokenizer, load_clip_model
from getEmbeddings import get_detailed_instruct, embed_texts, get_text_features
from evaluation import ndcg_at_k
import json
import requests


# Load the API key from credentials.json
with open('credentials.json') as f:
    credentials = json.load(f)
    api_key = credentials['api_key']

app = Flask(__name__)
es = Elasticsearch(["http://localhost:9200"])
index_name = "documents"

# Load models
mistral = 'intfloat/e5-mistral-7b-instruct'
Qwen2 = 'Alibaba-NLP/gte-Qwen2-7B-instruct'
clip = 'openai/clip-vit-large-patch14'

device = 'cuda' if torch.cuda.is_available() else 'cpu'

tokenizer_2 = load_tokenizer(mistral)
model_2 = load_model(mistral)
tokenizer_3 = load_tokenizer(Qwen2, trust_remote_code=True)
model_3 = load_model(Qwen2, trust_remote_code=True)
tokenizer_4, model_4 = load_clip_model(clip, device)

# Load topics DataFrame globally
topics_df = pd.read_csv('../dataset/TopRelevant_topics1.csv')
Manualtopics_df = pd.read_csv('../dataset/manual_topics.csv')

# In-memory storage for scores and LLM inputs
scores_storage = {}
llm_inputs = {}

@app.route('/')
def index():
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
    topic_embedding_2 = embed_texts(query, tokenizer_2, model_2, device)
    topic_embedding_3 = embed_texts(query, tokenizer_3, model_3, device)
    topic_embedding_4 = get_text_features(topic, tokenizer_4, model_4, device)

    # Elasticsearch BM25 query using multi_match for content and title
    script_query_1 = {
        "query": {
            "multi_match": {
                "query": topic,
                "fields": ["content", "title"],
                "type": "best_fields",
                "tie_breaker": 0.3
            }
        }
    }
    
    # Elasticsearch query for the first model
    script_query_2 = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'mistral_embedding') + 1.0",
                "params": {"query_vector": topic_embedding_2}
            }
        }
    }

    # Elasticsearch query for the second model
    script_query_3 = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'gte_embedding') + 1.0",
                "params": {"query_vector": topic_embedding_3}
            }
        }
    }

    # Elasticsearch query for the third model
    script_query_4 = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'clip_embedding') + 1.0",
                "params": {"query_vector": topic_embedding_4}
            }
        }
    }

    # Get results for the first model ie. BM25
    response_1 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_1["query"],
        "_source": ["title", "content", "image_data"]
    })

    # Get results for the mistral model
    response_2 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_2,
        "_source": ["title", "content", "image_data"]
    })

    # Get results for the qwen-2 model
    response_3 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_3,
        "_source": ["title", "content", "image_data"]
    })

    # Get results for the clip model
    response_4 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_4,
        "_source": ["title", "content", "image_data"]
    })

    documents_1 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"], "image_data": hit["_source"]["image_data"]} for hit in response_1['hits']['hits']]
    documents_2 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"], "image_data": hit["_source"]["image_data"]} for hit in response_2['hits']['hits']]
    documents_3 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"], "image_data": hit["_source"]["image_data"]} for hit in response_3['hits']['hits']]
    documents_4 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"], "image_data": hit["_source"]["image_data"]} for hit in response_4['hits']['hits']]
    
    return jsonify({
        "model_1_documents": documents_1,
        "model_2_documents": documents_2,
        "model_3_documents": documents_3,
        "model_4_documents": documents_4
    })

@app.route('/get-random-image', methods=['GET'])
def get_random_image():
    total_docs = es.count(index=index_name)['count']

    max_offset = min(total_docs, 10000) - 1
    random_offset = random.randint(0, max_offset)

    response = es.search(index=index_name, body={
        "size": 1,
        "query": {"match_all": {}},
        "from": random_offset,
        "_source": ["image_data","title"]
    })
    
    if response['hits']['hits']:
        doc = response['hits']['hits'][0]['_source']
        return jsonify({"image_data": doc['image_data'], "title": doc.get('title', 'No Title')})
    else:
        return jsonify({"error": "No documents found"}), 404

@app.route('/store-scores', methods=['POST'])
def store_scores():
    data = request.json
    scores_storage.update(data)
    return jsonify({"message": "Scores stored successfully"})

@app.route('/retrieve-scores', methods=['GET'])
def retrieve_scores():
    return jsonify(scores_storage)

@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.json
    results = data
    k = 3

    # Collect all relevance scores from all models
    all_relevance_scores = []
    for model_key, documents in results.items():
        if model_key != 'query' and '_documents' in model_key:
            all_relevance_scores.extend([(doc['relevance'] + doc['completeness']) for doc in documents])

    ndcg_scores = {}
    for model_key, documents in results.items():
        if model_key != 'query' and '_documents' in model_key:
            relevance_scores = [(doc['relevance'] + doc['completeness']) for doc in documents[:k]]
            ndcg_score = ndcg_at_k(relevance_scores, k, all_relevance_scores)
            ndcg_scores[model_key] = ndcg_score

    # Store the NDCG scores in the scores_storage
    for model_key, score in ndcg_scores.items():
        scores_storage[model_key + '_ndcg'] = score

    return jsonify(ndcg_scores)

@app.route('/prepare-llm-input', methods=['GET'])
def prepare_llm_input():
    # Get the number of top documents to use from query parameters, default to 1
    top_n = int(request.args.get('top_n', 1))

    # Identify the model with the highest NDCG score
    ndcg_scores = {key: value for key, value in scores_storage.items() if key.endswith('_ndcg')}
    top_model = max(ndcg_scores, key=ndcg_scores.get).replace('_ndcg', '')

    # Extract the top-ranked documents from the top NDCG model
    top_documents_key = top_model.replace('_ndcg', '_documents')
    top_documents = scores_storage.get(top_documents_key, [])

    if not top_documents:
        return jsonify({"error": f"No documents found for model: {top_model}"}), 404

    query = scores_storage.get('query', 'No Query Found')

    # Sort documents by the sum of completeness, relevance, and score
    top_documents.sort(key=lambda doc: doc['score'], reverse=True)

    # Prepare the combined JSON payload from the top N documents
    content_text = ""
    for doc in top_documents[:top_n]:
        content_text += (
            f"Title: {doc['title']}\n"
            f"Content: {doc['content']}\n\n"
        )

    content = [
        {
            "type": "text",
            "text": (
                "Please provide a detailed and comprehensive statistical insight from the following titles, content, and the provided image data. "
                "Ensure the response includes a thorough analysis with context and evaluation. "
                "Conclude with a final decision. Format the response as a summary and avoid unnecessary newlines.\n\n"
                f"{content_text}\n"
                f"Query: {query}"
            )
        }
    ]

    # Append the images
    for doc in top_documents[:top_n]:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{doc['image_data']}"
                }
            }
        )

    messages = [
    {
        "role": "user",
        "content": content
    }
    ]

    payload = {
        "model": "gpt-4o",
        "messages": messages,
        "max_tokens": 1000
    }
    
    # Print the payload to check the order
    llm_input = json.dumps(payload, indent=1)
    # print(llm_input)
    
    # Store the payload in llm_inputs
    llm_inputs.update(payload)
    
    return jsonify({"message": "LLM input prepared and stored successfully"})

@app.route('/retrieve-llm-input', methods=['GET'])
def retrieve_llm_input():
    return jsonify(llm_inputs)

@app.route('/generate-llm-answer', methods=['POST'])
def generate_llm_answer():
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    if not llm_inputs:
        return jsonify({"error": "No LLM input found"}), 404

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=llm_inputs)
    answer = response.json()

    scores_storage['llm_answer'] = answer  # Store the generated answer in scores_storage

    return jsonify(answer)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
    # app.run(host='0.0.0.0', port=5000, debug=True)
