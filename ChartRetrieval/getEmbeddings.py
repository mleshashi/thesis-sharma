import torch
import torch.nn.functional as F
from torch import Tensor

# Function to perform last token pooling on hidden states based on the attention mask.
# It handles cases with left or right padding.
def last_token_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
    if left_padding:
        return last_hidden_states[:, -1]
    else:
        sequence_lengths = attention_mask.sum(dim=1) - 1
        batch_size = last_hidden_states.shape[0]
        return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]
    
# Function to format a detailed instruction string from a task description and query.
def get_detailed_instruct(task_description: str, query: str) -> str:
    return f'Instruct: {task_description}\nQuery: {query}'

max_length=1250


# Function to embed texts
def embed_texts(texts, tokenizer, model, device):
    input_token = tokenizer(texts, max_length=max_length, padding=True, truncation=True, return_tensors='pt')
    input_token = {k: v.to(device) for k, v in input_token.items()}
    with torch.no_grad():  # Ensure no gradients are calculated
        outputs = model(**input_token)
        embeddings = last_token_pool(outputs.last_hidden_state, input_token['attention_mask'])
        embeddings = F.normalize(embeddings, p=2, dim=1)
    return embeddings.detach().cpu().numpy().flatten().tolist()



def get_text_features(texts, tokenizer, model, device):
    """
    Preprocesses a text query, extracts text features using the model, and normalizes the features.

    Args:
        text_query (str): The input text query.
        tokenizer: The tokenizer to use for preprocessing the text.
        model: The model to use for extracting text features.
        device (str): The device to run the model on ('cuda' or 'cpu').

    Returns:
        list: Normalized text features as a list of numpy arrays.
    """
    # Tokenize the text query
    inputs = tokenizer(text=[texts], padding=True, return_tensors="pt").to(device)
    
    # Extract text features
    with torch.no_grad():
        text_features = model.get_text_features(**inputs).squeeze(0)
        # Normalize the features
        text_features = (text_features / text_features.norm(p=2, dim=-1, keepdim=True)).cpu().numpy().tolist()
    
    return text_features
