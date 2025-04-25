import asyncio
import os
import torch
import time
import json
import re
from typing import List, Dict, Any


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
# Chunk text with overlap
def chunk_text_with_overlap(text: str, chunk_size: int, overlap_size: int) -> List[str]:
    """
    Splits a large text string into smaller chunks with overlap (character-based).

    Args:
        text (str): The input text string.
        chunk_size (int): The target size of each chunk in characters.
        overlap_size (int): The size of the overlap between consecutive chunks in characters.

    Returns:
        List[str]: A list of text chunks.
    """
    if chunk_size <= overlap_size < 0 or overlap_size >= chunk_size:
        print(f"Error: Invalid Chunk Params.")
        return [text]
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:min(end, text_len)]
        chunks.append(chunk)
        
        # Calc of next chunk, with overlapping
        start += chunk_size - overlap_size
        
        # Avoid goin backwards if overlap is very large
        if start < len(chunks[-1]) - overlap_size and len(chunks) > 1:
            break
        
    # Ensure loop doesnt create empty last chunk
    if chunks and not chunks[-1]:
        chunks.pop()
        
    print(f"Split text into {len(chunks)} chunks (size={chunk_size}, overlap={overlap_size}).")
    return chunks


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
    
    try: 
        print("Start LLM Sumamry...")
        
        # Tokenize the prompt
        inputs = llm_tokenizer_instance(
            prompt, 
            return_tensors="pt", 
            padding=True,
            truncation=True,
            max_length=llm_tokenizer_instance.model_max_length
        ).to(DEVICE)
        
        # Run Sync model gen in thread pool
        # llm_model_instance.generate -- is blocking call
        output_tokens = await loop.run_in_executor(
            None,
            llm_model_instance.generate,
            inputs.input_ids,
            attention_mask=inputs.attention_mask,
            **generation_params
        )
        
        print("...End LLM Summary")
        
        # Decode from token to text
        # Slice to remove the input prompt tokens from the output
        generated_text = llm_tokenizer_instance.decode(
            output_tokens[0][inputs.input_ids.shape[-1]:],
            skip_special_tokens=True
        )
        
        print("LLM Output Ready")
        return generated_text
    
    except Exception as e:
        print(f"Error occurred during LLM Summary: {e}")
        return f"Error during LLM Summary: {e}"
    
# --- Helper
# Parse the LLM output
def parse_llm_output(llm_output_text: str) -> dict:
    """ 
    Parse the LLM text based on the expected struct
    """
    
    print("Starting LLM output parse...")
    parsed_data = {
        "main_topic": "",
        "summary": "",
        "key_points": [],
        "tasks_to_complete": []
    }
    
    markers = {
        "main_topic": "[MAIN TOPIC]",
        "summary": "[SUMMARY]",
        "key_points": "[KEY POINTS]",
        "tasks_to_complete": "[TASKS TO COMPLETE]"
    }
    
    # Use regex to find content between markers
    main_topic_match = re.search(rf"{re.escape(markers['main_topic'])}(.*?){re.escape(markers['summary'])}", llm_output_text, re.DOTALL)
    summary_match = re.search(rf"{re.escape(markers['summary'])}(.*?){re.escape(markers['key_points'])}", llm_output_text, re.DOTALL)
    key_points_match = re.search(rf"{re.escape(markers['key_points'])}(.*?){re.escape(markers['tasks_to_complete'])}", llm_output_text, re.DOTALL)
    tasks_to_complete_match = re.search(rf"{re.escape(markers['tasks_to_complete'])}(.*?)", llm_output_text, re.DOTALL)
    
    if main_topic_match:
        parsed_data["main_topic"] = main_topic_match.group(1).strip()
    
    if summary_match:
        parsed_data["summary"] = summary_match.group(1).strip()
    
    if key_points_match:
        key_points_block = key_points_match.group(1).strip()
        parsed_data["key_points"] = [
            line.strip() for line in key_points_block.split("\n")
            if line.strip() and (line.strip().startswith("-") or line.strip().startswith("*"))
        ]
        
    if tasks_to_complete_match:
        tasks_to_complete_block = tasks_to_complete_match.group(1).strip()
        parsed_data["tasks_to_complete"] = [
            line.strip() for line in tasks_to_complete_block.split("\n")
            if line.strip() and (line.strip().startswith("-") or line.strip().startswith("*"))
        ]
        
    print("...End LLM output parse")
    return parsed_data

# --- Main Summarization Pipeline
async def run(merged_segments: list[dict]) -> dict | None:
    """ 
    Runs the summarization pipeline: 
        Formats Transcript
        Prompts LLM
        Parses Output
        
    Args:
        merged_segments (list[dict]): The list of merged transcription and diarization segments.

    Returns:
        dict | None: A dictionary containing the structured summary (main_topic, summary, key_points, tasks_to_complete), or None on failure.
                     If merging resulted in no segments, returns a specific structure indicating that.
    """
    
    global llm_model_instance, llm_tokenizer_instance
    
    if llm_model_instance is None or llm_tokenizer_instance is None:
        print("Error: LLM Model or Tokenizer not loaded")
        return {"Error": "Summarization model not loaded"}
    
    if not merged_segments:
        print("No merged segments provided")
        return {
            "main_topic": "No audio content",
            "summary": "The audio cintained no discernible speech",
            "key_points": [],
            "tasks_to_complete": []
        }
        
    # Step 1: Format Transcript
    transcript_text = format_transcript_for_llm(merged_segments)
    
    # Define chunk params
    
    # Step 2: Define the prompt
    llm_prompt = get_summarization_prompt(transcript_text)
    
    # Step 3: Run LLM Async
    llm_generated_text = await generate_summary_async(llm_prompt)
    
    if llm_generated_text.startswith("Error during LLM Summary"):
        print(f"LLM Generation Failed: {llm_generated_text}")
        return {
            "error": llm_generated_text,
            "main_topic": "Summarization Failed",
            "summary": llm_generated_text,
            "key_points": [],
            "tasks_to_complete": []
        }
        
    # Step 4: Parse LLM Output
    # Parsing can fail if LLM doesnt follow format
    try: 
        structured_summary = parse_llm_output(llm_generated_text)
        return structured_summary
    except Exception as e:
        print(f"Error parsing LLM output: {e}")
        print(f"LLM Output Text: \n---\n{llm_generated_text}\n---")
        return {
            "error": f"Failed to Parse LLM Ouput: {e}",
            "main_topic": "Parsing Failed",
            "summary": "Failed to parse the summary from the LLM output",
            "key_points": [],
            "tasks_to_complete": [],
            "raw_llm_output": llm_generated_text
        }
    