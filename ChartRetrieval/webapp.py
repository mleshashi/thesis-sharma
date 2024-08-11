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
from collections import defaultdict
import random

# Load the API key from credentials.json
with open('credentials.json') as f:
    credentials = json.load(f)
    api_key1 = credentials['gpt-api_key']
    api_key2 = credentials['lama-api_key']

app = Flask(__name__)
es = Elasticsearch(["http://localhost:9200"])
index_name = "documents"

# Load models
mistral = 'intfloat/e5-mistral-7b-instruct'
Qwen2 = 'Alibaba-NLP/gte-Qwen2-7B-instruct'
clip = 'openai/clip-vit-large-patch14'

device = 'cuda' if torch.cuda.is_available() else 'cpu'

tokenizer_1, model_1 = load_clip_model(clip, device)
tokenizer_2 = load_tokenizer(mistral)
model_2 = load_model(mistral)
tokenizer_3 = load_tokenizer(Qwen2, trust_remote_code=True)
model_3 = load_model(Qwen2, trust_remote_code=True)

# Load topics DataFrame globally
topics_df = pd.read_csv('../dataset/Touche.csv')
Manualtopics_df = pd.read_csv('../dataset/manual_topics.csv')

# In-memory storage for scores and search results
search_results = {}
scores_storage = {}
llm_inputs = {}
llm_answers = {}
top_documents_storage = {}
metric_metadata = {} # Store metadata for the metrics
old_data = None  # Initialize old_data globally

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
    topic_embedding_1 = get_text_features(topic, tokenizer_1, model_1, device)
    topic_embedding_2 = embed_texts(query, tokenizer_2, model_2, device)
    topic_embedding_3 = embed_texts(query, tokenizer_3, model_3, device)

    # Elasticsearch BM25 query using multi_match for content and title
    script_query_1 = {
        "query": {
            "multi_match": {
                "query": topic,
                "fields": ["title", "content"],
                "type": "best_fields",
                "tie_breaker": 0.3
            }
        }
    }

    # Elasticsearch BM25 query using multi_match for lava content and title
    script_query_2 = {
        "query": {
            "multi_match": {
                "query": topic,
                "fields": ["title", "lava_content"],
                "type": "best_fields",
                "tie_breaker": 0.3
            }
        }
    }

    # Elasticsearch query using clip model on the image embeddings
    script_query_3 = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'image_embedding') + 1.0",
                "params": {"query_vector": topic_embedding_1}
            }
        }
    }
    
    # Elasticsearch query for the first model
    script_query_4 = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'mistral_embedding') + 1.0",
                "params": {"query_vector": topic_embedding_2}
            }
        }
    }

    # Elasticsearch query for the second model
    script_query_5 = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'llava_content_embedding') + 1.0",
                "params": {"query_vector": topic_embedding_2}
            }
        }
    }

    # Elasticsearch query for the third model
    script_query_6 = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'gte_embedding') + 1.0",
                "params": {"query_vector": topic_embedding_3}
            }
        }
    }

    # Get results for the first model ie. BM25 on title and content
    response_1 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_1["query"],
        "_source": ["title", "content", "image_data"]
    })

    # Get results for the second model ie. BM25 on title and llava content
    response_2 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_2["query"],
        "_source": ["title", "content", "image_data"]
    })

    # Get results for the clip model on the image embeddings
    response_3 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_3,
        "_source": ["title", "content", "image_data"]
    })

    # Get results for the mistral model on the title and content embeddings
    response_4 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_4,
        "_source": ["title", "content", "image_data"]
    })

    # Get results for the mistral model on the title and llava content embeddings
    response_5 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_5,
        "_source": ["title", "content", "image_data"]
    })
        
    # Get results for the qwen-2 model on the title and content embeddings
    response_6 = es.search(index=index_name, body={
        "size": 3,  # Fetch top 3 relevant documents
        "query": script_query_6,
        "_source": ["title", "content", "image_data"]
    })

    documents_1 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"], "image_data": hit["_source"]["image_data"]} for hit in response_1['hits']['hits']]
    documents_2 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"], "image_data": hit["_source"]["image_data"]} for hit in response_2['hits']['hits']]
    documents_3 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"], "image_data": hit["_source"]["image_data"]} for hit in response_3['hits']['hits']]
    documents_4 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"], "image_data": hit["_source"]["image_data"]} for hit in response_4['hits']['hits']]
    documents_5 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"], "image_data": hit["_source"]["image_data"]} for hit in response_5['hits']['hits']]
    documents_6 = [{"title": hit["_source"]["title"], "content": hit["_source"]["content"], "score": hit["_score"], "image_data": hit["_source"]["image_data"]} for hit in response_6['hits']['hits']]
    
    # Store results in memory without the "latest" wrapper
    search_results.update({
        "query": topic,
        "BM25_documents": documents_1,
        "BM25-llava_documents": documents_2,
        "Clip_documents": documents_3,
        "Mistral_documents": documents_4,
        "Mistral-llava_documents": documents_5,
        "Qwen2_documents": documents_6
    })
    
    return jsonify(search_results)

@app.route('/retrieve-results', methods=['GET'])
def retrieve_results():
    return jsonify(search_results)

@app.route('/save-annotations', methods=['POST'])
def save_annotations():
    data  = request.json
    # Extract annotator details
    annotator_name = data.get('annotatorName')
    annotations = data.get('annotations', [])

    # Store the annotator details separately
    search_results['annotator_details'] = {
        "annotator_name": annotator_name,
        "affiliated": "Bauhaus-Universität Weimar"
    }

    # save the annotator details in the metric_metadata
    metric_metadata['annotator_name'] = annotator_name

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
    unique_doc_count = 0  # Variable to count unique documents

    for model_key, documents in results.items():
        if model_key != 'query' and '_documents' in model_key:
            for doc in documents:
                doc_key = (doc['title'].strip(), doc['content'].strip())
                if doc_key not in seen_docs:
                    seen_docs.add(doc_key)
                    all_relevance_scores.append(doc['relevance'] + doc['completeness'])
                    unique_doc_count += 1  # Increment the unique document count

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

        
    # Add unique document count to the metadata
    metric_metadata['unique_document'] = unique_doc_count

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
    
    # Group the scores
    score_groups = defaultdict(list)
    for key, value in ndcg_scores.items():
        score_groups[value].append(key)

    # Sort the groups by score in descending order
    sorted_score_groups = sorted(score_groups.items(), key=lambda item: item[0], reverse=True)

    # Randomize within each group
    randomized_models = []
    for score, models in sorted_score_groups:
        random.shuffle(models)
        for model in models:
            randomized_models.append((model, score))
    
    top_model, highest_ndcg_score = randomized_models[0]
    top_model = top_model.replace(ndcg_key, '')
    top_model_name = top_model.replace('_documents', '')
    
    second_top_model, second_highest_ndcg_score = randomized_models[1]
    second_top_model = second_top_model.replace(ndcg_key, '')
    second_top_model_name = second_top_model.replace('_documents', '')

    third_top_model, third_highest_ndcg_score = randomized_models[2]
    third_top_model = third_top_model.replace(ndcg_key, '')
    third_top_model_name = third_top_model.replace('_documents', '')
    
    print(ndcg_key, top_model_name, highest_ndcg_score)
    print(ndcg_key, second_top_model_name, second_highest_ndcg_score)
    print(ndcg_key, third_top_model_name, third_highest_ndcg_score)

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
                "You are an expert statistical analyst. Answer the given query with a detailed and comprehensive statistical insight from the following title, content, and provided image data.\n\n"
                f"Query: {query}\n"
                f"{content_text}\n"
                "Format the response in the following structure with 3 paragraphs, without paragraph title::\n\n"
                "1. Start the response with a clear classification or a straightforward answer to the query.\n"
                "2. Provide supporting findings and detailed analysis, including relevant statistical data.\n"
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

    messages1 = [
    {
        "role": "user",
        "content": content
    }
    ]

    # Create the instruction and user messages
    messages2 = [
        {
            "role": "system",
            "content": (
                "You are an expert statistical analyst. Answer the given query with a detailed and comprehensive statistical insight from the following title and content.\n\n"
                "Format the response in the following structure with 3 paragraphs, without paragraph title:\n\n"
                "1. Start the response with a clear classification or a straightforward answer to the query.\n"
                "2. Provide supporting findings and detailed analysis, including relevant statistical data.\n"
                "3. Summarize the final conclusion briefly."
            )
        },
        {
            "role": "user",
            "content": f"Query: {query}\n\n{content_text}"
        }
    ]

    # Create two separate payloads with the same message but different models
    payload1 = {
        "model": "gpt-4o",
        "messages": messages1,
        "max_tokens": 1000
    }

    payload2 = {
        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
        "messages": messages2,
        "max_tokens": 1000
    }
    
    # Store the payloads in llm_inputs
    llm_inputs['gpt'] = payload1
    llm_inputs['lama'] = payload2

    # Store the top documents in a separate storage
    top_documents_storage['top_documents'] = top_documents[:top_n]

    # Store the NDCG metric, top model, and highest NDCG score in metadata 
    metric_metadata['ndcg_metric'] = ndcg_key
    metric_metadata['top_model'] = top_model_name
    metric_metadata['highest_ndcg_score'] = highest_ndcg_score
    metric_metadata['second_top_model'] = second_top_model_name
    metric_metadata['second_highest_ndcg_score'] = second_highest_ndcg_score
    metric_metadata['third_top_model'] = third_top_model_name
    metric_metadata['third_highest_ndcg_score'] = third_highest_ndcg_score

    return jsonify({"message": "LLM input prepared and stored successfully"})


@app.route('/retrieve-llm-input', methods=['GET'])
def retrieve_llm_input():
    return jsonify(llm_inputs)

@app.route('/retrieve-top-documents', methods=['GET'])
def retrieve_top_documents():
    return jsonify(top_documents_storage)


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
    input_lama = llm_inputs.get('lama', {})

    response1 = requests.post("https://api.openai.com/v1/chat/completions", headers=headers1, json=input_gpt)
    response2 = requests.post("https://api.deepinfra.com/v1/openai/chat/completions", headers=headers2, json=input_lama)
    
    # Parse the responses
    answer_gpt = response1.json()
    answer_lama = response2.json()

    # Store the generated answers in scores_storage
    llm_answers['gpt_llm_answer'] = answer_gpt
    llm_answers['lama_llm_answer'] = answer_lama

    return jsonify({
        "gpt_answer": answer_gpt,
        "lama_answer": answer_lama
    })

@app.route('/retrieve-llm-answers', methods=['GET'])
def retrieve_llm_answers():
    return jsonify(llm_answers)

@app.route('/save-llm-answers', methods=['POST'])
def save_llm_answers():
    scores = request.json

    # Update the global llm_answers with the received data
    for key, value in scores.items():
        if key in llm_answers:
            llm_answers[key]['annotation'] = value.get('annotation', {})
        else:
            llm_answers[key] = value

    # Optionally, persist llm_answers to a file or database
    with open('llm_answers_with_annotations.json', 'w') as f:
        json.dump(llm_answers, f)

    return jsonify({"message": "LLM answers and annotations saved successfully"})

# Ensure the directories exist
os.makedirs('../dataset/annotations', exist_ok=True)

@app.route('/save-query', methods=['POST'])
def save_query():
    # Use the global old_data to persist it across requests
    global old_data  

    # Retrieve the necessary data from the in-memory storage
    query = scores_storage.get('query', 'No Query Found')
    ndcg_metric = metric_metadata.get('ndcg_metric', 'No Metric Found')
    top_model = metric_metadata.get('top_model', 'No Model Found')
    highest_ndcg_score = metric_metadata.get('highest_ndcg_score', 'No Score Found')
    second_top_model = metric_metadata.get('second_top_model', 'No Model Found')
    second_highest_ndcg_score = metric_metadata.get('second_highest_ndcg_score', 'No Score Found')
    third_top_model = metric_metadata.get('third_top_model', 'No Model Found')
    third_highest_ndcg_score = metric_metadata.get('third_highest_ndcg_score', 'No Score Found')

    gpt_answer = llm_answers.get('gpt_llm_answer', {}).get('choices', [{}])[0].get('message', {}).get('content', 'No Answer Found').replace('\n', ' ').replace('\r', ' ')
    relevance_score_gpt = int(llm_answers.get('gpt_llm_answer', {}).get('annotation', {}).get('relevance'))
    faithfulness_gpt = int(llm_answers.get('gpt_llm_answer', {}).get('annotation', {}).get('faithfulness'))
    
    lama_answer = llm_answers.get('lama_llm_answer', {}).get('choices', [{}])[0].get('message', {}).get('content', 'No Answer Found').replace('\n', ' ').replace('\r', ' ')
    relevance_score_lama = int(llm_answers.get('lama_llm_answer', {}).get('annotation', {}).get('relevance'))
    faithfulness_lama = int(llm_answers.get('lama_llm_answer', {}).get('annotation', {}).get('faithfulness'))

    annotator_name = metric_metadata.get('annotator_name', 'No Annotator Found')
    Unique_document = metric_metadata.get('unique_document', 'No Unique Document Found')

    # Check if first and second model NDCG scores are the same
    if highest_ndcg_score == second_highest_ndcg_score and highest_ndcg_score == third_highest_ndcg_score:
        scores_equal = '1&2&3'
    elif highest_ndcg_score == second_highest_ndcg_score:
        scores_equal = '1&2'
    else:
        scores_equal = 'None'

    


    # Define the path to the CSV file
    csv_file_path  = '../dataset/results/results.csv'

    # Check if the CSV file exists
    file_exists = os.path.isfile(csv_file_path )

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
        'ndcg_metric': ndcg_metric,
        'top_model': top_model,
        'highest_ndcg_score': highest_ndcg_score,
        'second_top_model': second_top_model,
        'second_highest_ndcg_score': second_highest_ndcg_score,
        'third_top_model': third_top_model,
        'third_highest_ndcg_score': third_highest_ndcg_score,
        'final_answer_gpt': gpt_answer,
        'relevance_gpt': relevance_score_gpt,
        'faithfulness_gpt': faithfulness_gpt,
        'final_answer_lama': lama_answer,
        'relevance_lama': relevance_score_lama,
        'faithfulness_lama': faithfulness_lama,
        'annotator_name': annotator_name,
        'scores_equal': scores_equal,
        'Unique_document': Unique_document
    }

    # Convert the data to a DataFrame
    df = pd.DataFrame([data])

    # Append the data to the CSV file
    if file_exists:
        df.to_csv(csv_file_path, mode='a', header=False, index=False)
    else:
        df.to_csv(csv_file_path, mode='w', header=True, index=False)


    # Save scores_storage as a separate JSON file with the filename as the query
    safe_query = "".join([c if c.isalnum() else "_" for c in query])  # Ensure the filename is safe
    json_file_path = f'../dataset/annotations/{safe_query}.json'
    with open(json_file_path, 'w') as json_file:
        json.dump(scores_storage, json_file, indent=4)

    return jsonify({"message": "Query saved successfully."})


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
    # app.run(host='0.0.0.0', port=5000, debug=True)
