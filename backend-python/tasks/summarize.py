import asyncio
import os
import torch
import time
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

        try:
            # --- Quantization Config
            # Configure 4-bit quantization for reduced VRAM/Mem usage
            
            if DEVICE == "cuda":
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                    # bnb_4bit_compute_dtype=torch.bfloat16 -- use only if server has NVIDIA GPU
                )
            else:
                bnb_config = None
                
            # --- Load Tokenizer
            llm_tokenizer_instance = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
            
            if llm_tokenizer_instance.pad_token is None:
                llm_tokenizer_instance.pad_token = llm_tokenizer_instance.eos_token
                
            # --- Load Model
            if bnb_config:
                llm_model_instance = AutoModelForCasualLM.from_pretrained(
                    LLM_MODEL_NAME,
                    quantization_config=bnb_config,
                    device_map="auto"
                )
            else:
                llm_model_instance = AutoModelForCasualLM.from_pretrained(
                    LLM_MODEL_NAME,
                    device_map="cpu" if DEVICE == "cpu" else "cuda"
                )
                
            llm_model_instance.eval()
            
            print(f"LLM model '{LLM_MODEL_NAME}' loaded successfully")
            
        except Exception as e:
            print(f"Fatal Error: Failed to load LLM '{LLM_MODEL_NAME}': {e}")
            
            llm_model_instance = None
            llm_tokenizer_instance = None
            
# --- Helper Function
# Format Transcript for LLM
def format_transcript_for_llm(merged_segments: list[dict]) -> str:
    """ 
    Formats the list of merged segments into a single text string for the LLM
    Includes timestamps & speaker labels
    """
    
    if not merged_segments:
        return "## Empty Transcript ##"
    
    formatted_text = "Meeting Transcript:\n\n"
    for segment in merged_segments:
        # Check segment has expected keys, use .get for safety
        speaker = segment.get("speaker", "Unkown Speaker")
        start_time = segment.get("start", 0.0)
        end_time = segment.get("end", 0.0)
        text = segment.get("text", "").strip()
        
        # Format timestamp (HH:MM:SS)
        start_timestamp = time.strftime('%H:%M:%S' , time.gmtime(start_time))
        end_timestamp = time.strftime('%H:%M:%S' , time.gmtime(end_time))
        
        if text:
            formatted_text += f"[{start_timestamp} - {end_timestamp}] {speaker}: {text}\n"
        else:
            formatted_text += f"[{start_timestamp} - {end_timestamp}] Error Processing: {text}\n"
            
    # Limit input length for model context window
    
    # *** 32K context window for Mistral 7B v0.2 == ROUGHLY 128,000 char ***
    max_chars = 100000
    if len(formatted_text) > max_chars:
        print(f"Warning: Transcript Length ({len(formatted_text)} chars) exceeds rough limit ({max_chars})")
        formatted_text = formatted_text[:max_chars] + "\n[... Transcript Truncated ...]"
    
    return formatted_text

# --- Helper Function
# Define LLM Prompt
