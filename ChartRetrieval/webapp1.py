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
import os

# Load the API key from credentials.json
with open('credentials.json') as f:
    credentials = json.load(f)
    api_key1 = credentials['gpt-api_key']
    api_key2 = credentials['llava-api_key']

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
#tokenizer_3 = load_tokenizer(Qwen2, trust_remote_code=True)
#model_3 = load_model(Qwen2, trust_remote_code=True)
tokenizer_4, model_4 = load_clip_model(clip, device)

# Load topics DataFrame globally
topics_df = pd.read_csv('../dataset/TopRelevant_topics1.csv')
Manualtopics_df = pd.read_csv('../dataset/manual_topics.csv')

# In-memory storage for scores and search results
search_results = {}
scores_storage = {}
llm_inputs = {}

@app.route('/')
def index():
    return render_template('main-page.html')

@app.route('/annotation')
def annotation():
    return render_template('annotation.html')

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
    topic_embedding_3 = embed_texts(query, tokenizer_2, model_2, device)
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
                "source": "cosineSimilarity(params.query_vector, 'mistral_embedding') + 1.0",
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
    
    # Store results in memory without the "latest" wrapper
    search_results.update({
        "query": topic,
        "model_1_documents": documents_1,
        "model_2_documents": documents_2,
        "model_3_documents": documents_3,
        "model_4_documents": documents_4
    })
    
    return jsonify(search_results)

@app.route('/retrieve-results', methods=['GET'])
def retrieve_results():
    return jsonify(search_results)

@app.route('/save-annotations', methods=['POST'])
def save_annotations():
    annotations = request.json

    for model_key, documents in search_results.items():
        for doc in documents:
            updated = False  # Flag to indicate if the document was updated
            if isinstance(doc, dict):
                for annotation in annotations:
                    if (''.join(doc.get('title', '').split()) == ''.join(annotation.get('title', '').split()) and
                        ''.join(doc.get('content', '').split()) == ''.join(annotation.get('content', '').split())):
                        doc['relevance'] = int(annotation.get('relevance', 0))
                        doc['completeness'] = int(annotation.get('completeness', 0))
                        updated = True
                        break
                if not updated:
                    print(f"Document did not match any annotation: {doc}")
                    for annotation in annotations:
                        print(f"Compared with annotation: {annotation}")

    return jsonify({"message": "Annotations saved successfully"})


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
    ks = [1, 2, 3]  # List of k values to evaluate

    # Collect all relevance scores from all models, removing duplicates
    all_relevance_scores = []
    seen_docs = set()  # To keep track of seen (title, content) pairs

    for model_key, documents in results.items():
        if model_key != 'query' and '_documents' in model_key:
            for doc in documents:
                doc_key = (doc['title'].strip(), doc['content'].strip())
                if doc_key not in seen_docs:
                    seen_docs.add(doc_key)
                    all_relevance_scores.append(doc['relevance'] + doc['completeness'])

     # Calculate NDCG scores for each k in ks
    ndcg_scores = {k: {} for k in ks}
    for model_key, documents in results.items():
        if model_key != 'query' and '_documents' in model_key:
            for k in ks:
                relevance_scores = [(doc['relevance'] + doc['completeness']) for doc in documents[:k]]
                ndcg_score = ndcg_at_k(relevance_scores, k, all_relevance_scores)
                ndcg_scores[k][model_key] = ndcg_score

    # Store the NDCG scores in the scores_storage
    for k in ks:
        for model_key, score in ndcg_scores[k].items():
            scores_storage[model_key + f'_ndcg@{k}'] = score

    return jsonify(ndcg_scores)

@app.route('/prepare-llm-input', methods=['GET'])
def prepare_llm_input():
    # Get the NDCG value to use from query parameters, default to 1
    ndcg_value = int(request.args.get('ndcg', 1))

    # Map the NDCG value to the number of documents
    top_n = ndcg_value

    # Identify the model with the highest NDCG score for the selected NDCG value
    ndcg_key = f'_ndcg@{ndcg_value}'
    ndcg_scores = {key: value for key, value in scores_storage.items() if key.endswith(ndcg_key)}
    if not ndcg_scores:
        return jsonify({"error": f"No NDCG scores found for NDCG@{ndcg_value}"}), 404
    
    top_model = max(ndcg_scores, key=ndcg_scores.get).replace(ndcg_key, '')

    # Extract the top-ranked documents from the top NDCG model
    top_documents_key = top_model.replace(ndcg_key, '_documents')
    top_documents = scores_storage.get(top_documents_key, [])

    if not top_documents:
        return jsonify({"error": f"No documents found for model: {top_model}"}), 404

    query = scores_storage.get('query', 'No Query Found')

    # Sort the documents by the score
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
                "Answer the given query with a detailed and comprehensive statistical insight from the following title, content, and provided image data.\n\n"
                f"Query: {query}\n"
                f"{content_text}\n"
                "Format the response in the following structure with 3 paragraphs:\n\n"
                "1. Start the response with a clear classification or a straightforward answer with respect to the query.\n"
                "2. Follow with supporting findings and detailed analysis.\n"
                "3. Summarize the final conclusion briefly."
            )
        }
    ]

    # Append the images in content
    for doc in top_documents[:top_n]:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{doc['image_data']}"
                }
            }
        )

    content2 = []

    # Append the images first
    for doc in top_documents[:top_n]:
        content2.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{doc['image_data']}"
                }
            }
        )

    # Append the text to content2
    content2.append(
        {
            "type": "text",
            "text": (
                "Answer the given query with a detailed and comprehensive statistical insight from the following title, content, and provided image data.\n\n"
                f"Query: {query}\n"
                f"{content_text}\n"
                "Format the response in the following structure with 3 paragraphs:\n\n"
                "1. Start the response with a clear classification or a straightforward answer with respect to the query.\n"
                "2. Follow with supporting findings and detailed analysis.\n"
                "3. Summarize the final conclusion briefly."
            )
        }
    )

    messages = [
    {
        "role": "user",
        "content": content
    }
    ]

    messages2 = [
    {
        "role": "user",
        "content": content2
    }
    ]

    # Create two separate payloads with the same message but different models
    payload1 = {
        "model": "gpt-4o",
        "messages": messages,
        "max_tokens": 1000
    }

    payload2 = {
        "model": "llava-hf/llava-1.5-7b-hf",
        "messages": messages2,
        "max_tokens": 1000
    }
    
     # Print the payloads to check the order
    llm_input1 = json.dumps(payload1, indent=1)
    llm_input2 = json.dumps(payload2, indent=1)
    print(llm_input1)
    print(llm_input2)
    
    # Store the payloads in llm_inputs
    llm_inputs['gpt'] = payload1
    llm_inputs['llava'] = payload2

    return jsonify({"message": "LLM input prepared and stored successfully"})


@app.route('/retrieve-llm-input', methods=['GET'])
def retrieve_llm_input():
    return jsonify(llm_inputs)


@app.route('/generate-llm-answer', methods=['POST'])
def generate_llm_answer():
# Define the headers for both API requests
    headers1 = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key1}"
    }
    headers2 = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key2}"
    }

    if not llm_inputs:
        return jsonify({"error": "No LLM input found"}), 404
    
    # Get the inputs for both APIs
    input_gpt = llm_inputs.get('gpt', {})
    input_llava = llm_inputs.get('llava', {})

    response1 = requests.post("https://api.openai.com/v1/chat/completions", headers=headers1, json=input_gpt)
    response2 = requests.post("https://api.deepinfra.com/v1/openai/chat/completions", headers=headers2, json=input_llava)
    
    # Parse the responses
    answer_gpt = response1.json()
    answer_llava = response2.json()

    # Store the generated answers in scores_storage
    scores_storage['gpt_llm_answer'] = answer_gpt
    scores_storage['llava_llm_answer'] = answer_llava

    return jsonify({
        "gpt_answer": answer_gpt,
        "llava_answer": answer_llava
    })


@app.route('/save-query', methods=['POST'])
def save_query():
    # Retrieve the necessary data from the in-memory storage
    query = scores_storage.get('query', 'No Query Found')
    ndcg_scores = {key: value for key, value in scores_storage.items() if key.endswith('_ndcg')}
    top_model = max(ndcg_scores, key=ndcg_scores.get).replace('_ndcg', '')
    highest_ndcg_score = ndcg_scores[top_model + '_ndcg']
    final_answer = scores_storage.get('llm_answer', {}).get('choices', [{}])[0].get('message', {}).get('content', 'No Answer Found')

    # Define the path to the CSV file
    csv_file_path = 'queries.csv'

    # Check if the CSV file exists
    file_exists = os.path.isfile(csv_file_path)

    # Determine the next SL number
    if file_exists:
        existing_df = pd.read_csv(csv_file_path)
        next_sl_number = existing_df.shape[0] + 1
    else:
        next_sl_number = 1

    # Prepare the data to append
    data = {
        'SL': next_sl_number,
        'query': query,
        'top_model': top_model,
        'highest_ndcg_score': highest_ndcg_score,
        'final_answer': final_answer
    }

    # Convert the data to a DataFrame
    df = pd.DataFrame([data])

    # Append the data to the CSV file
    if file_exists:
        df.to_csv(csv_file_path, mode='a', header=False, index=False)
    else:
        df.to_csv(csv_file_path, mode='w', header=True, index=False)

    return jsonify({"message": "Query saved successfully"})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
    # app.run(host='0.0.0.0', port=5000, debug=True)
