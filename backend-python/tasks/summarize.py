import asyncio
import os
import torch
import json
import re


from transformers import AutoModelForCasualLM, AutoTokenizer, BitsAndBytesConfig
from llama_cpp import Llama

# Getting token from env
from dotenv import load_dotenv
load_dotenv()

# Select LLM Model
LLM_MODEL_NAME = os.getenv("LLM_MODEL", "Mistral-7B-Instruct-v0.2")


# Detect device type
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load LLM on startup
llm_model_instance = None
llm_tokenizer_instance = None

def load_llm_model():
    """ 
    Loads the LLM model & tokenizer into memory
    Intended to be called once on startup
    """
    
    global llm_model_instance, llm_tokenizer_instance
    
    if llm_model_instance is None or llm_tokenizer_instance is None:
        print(f"Loading LLM model '{LLM_MODEL_NAME}' on device '{DEVICE}'")
        