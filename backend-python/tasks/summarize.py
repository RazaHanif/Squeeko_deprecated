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
def get_summarization_prompt(transcript_text: str) -> str:
    """ 
    Defines the prompt to instruct the LLM for summarization & structured output
    """
    
    prompt = f""" 
        You are an AI assitant tasked with analyzing a transcript, identifying the main topic, providing a concise summary, extracting key discussion points and listing any action itmes or tasks mentioned.
        
        Analyze the following transcript:
        
        ---
        {transcript_text}
        ---
        
        Please provice the output in the following structure, using the exact markers providied:
        [MAIN TOPIC]
        A concise, overarching topic of the discussion.
        
        [SUMMARY]
        A brief summary of the entire coverstaion, highlighting the most important themes and outcomes.
        
        [KEY POINTS]
        - A bulleted list of the main discussion points, decisions made, or significant information shared.
        
        [TASKS TO COMPLETE]
        - A bulleted list of any action items, tasks, or next steps mentioned during the meeting. For each task, if a person responsible is mentioned or implied, include thier name.
        
        Ensure you include all sections even if some are empty (e.g., no tasks mentioned).
    """
    
    return prompt

# --- Helper
# Run LLM Inference Async
async def generate_summary_async(prompt: str) -> str:
    """ 
    Runs the LLM text generation call in a thread pool    
    """
    
    global llm_model_instance, llm_tokenizer_instance
    
    if llm_model_instance is None or llm_tokenizer_instance is None:
        print("ErrorL LLM Model or Tokenizer not loaded")
        return "Error: LLM Model or Tokenizer not loaded"
    
    loop = asyncio.get_running_loop()
    
    # Define Generation Params
    generation_params = {
        "max_new_tokens": 500, # Maximum number of tokens to generate (summary length)
        "do_sample": True,     # Use sampling (more creative) vs. greedy decoding (more deterministic)
        "temperature": 0.7,    # Controls randomness (lower = more focused, higher = more creative) - use with do_sample=True
        "top_p": 0.9,          # Nucleus sampling threshold - use with do_sample=True
        "top_k": 50,           # Top-k sampling threshold - use with do_sample=True
        "attention_mask": None, # Handled by tokenizer/pipeline typically
        "pad_token_id": llm_tokenizer_instance.pad_token_id or llm_tokenizer_instance.eos_token_id, # Set padding token
        "eos_token_id": llm_tokenizer_instance.eos_token_id, # Set end of sequence token
        # Add other parameters as needed (e.g., num_beams for beam search, no_repeat_ngram_size)
    }
    