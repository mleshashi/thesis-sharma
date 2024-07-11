import torch
from transformers import AutoTokenizer, AutoModel, BitsAndBytesConfig, CLIPProcessor, CLIPModel
from torch import Tensor

# Quantization configuration
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

# Function to load tokenizer
def load_tokenizer(model_name, trust_remote_code=False):
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=trust_remote_code)
    return tokenizer

# Function to load model
def load_model(model_name, trust_remote_code=False):
    model = AutoModel.from_pretrained(
        model_name,
        quantization_config=quantization_config,
        device_map="auto",
        trust_remote_code=trust_remote_code
    )
    return model

# Function to load CLIP model
def load_clip_model(model_name, device):
    """
    Load CLIP processor and model.

    Args:
        model_name (str): Name of the pre-trained CLIP model to load.
        device (str): Device to load the model onto (e.g., 'cpu' or 'cuda').

    Returns:
        processor: The loaded CLIP processor.
        model: The loaded CLIP model.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name).to(device)
    return tokenizer, model

