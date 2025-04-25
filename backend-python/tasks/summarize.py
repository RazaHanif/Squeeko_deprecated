import asyncio
import os
import torch
import time
import json
import re
from typing import List, Dict, Any


from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

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
                llm_model_instance = AutoModelForCausalLM.from_pretrained(
                    LLM_MODEL_NAME,
                    quantization_config=bnb_config,
                    device_map="auto"
                )
            else:
                llm_model_instance = AutoModelForCausalLM.from_pretrained(
                    LLM_MODEL_NAME,
                    device_map="auto"
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
        speaker = segment.get("speaker", "Unknown Speaker")
        start_time = segment.get("start", 0.0)
        end_time = segment.get("end", 0.0)
        text = segment.get("text", "").strip()
        
        # Format timestamp (HH:MM:SS)
        start_timestamp = time.strftime('%H:%M:%S' , time.gmtime(start_time))
        end_timestamp = time.strftime('%H:%M:%S' , time.gmtime(end_time))
        
        if "error" in segment:
            formatted_text += f"[{start_timestamp} - {end_timestamp}] {speaker}: {text}\n"
        else:
            formatted_text += f"[{start_timestamp} - {end_timestamp}] Error Processing: {text}\n"
            
    return formatted_text

# --- Helper Function
# Chunk text with overlap
def chunk_text_with_overlap(text: str, chunk_size: int = 80000, overlap_size: int = 5000) -> List[str]:
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
        print("Error: Invalid Chunk Params.")
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
def get_llm_prompt(prompt_type: str, content: str) -> str:
    """ 
    Defines the prompt based on the type of summarization needed
    """
    
    if prompt_type == "final_structured_summary":
        instruction = f"""
Combine these summaries into a single, cohesive, structured summary including the overall Main Topic, a concice Summary of the entire meeting, a list of the most important Key Points discussed or decided, and a list of any Action Items or Tasks mentioned.

Summaries of different sections:

---
{content}
---

Provide the output using the exact markers provided:
[MAIN TOPIC]
A concise, overarching topic of the discussion derived from the summaries.

[SUMMARY]
A brief summary of the entire conversation based on the section summaries, highlighting the most important themes and outcomes.

[KEY POINTS]
- A bulleted list of the main discussion points, decisions made, or significant information shared across all sections.

[TASKS TO COMPLETE]
- A bulleted list of any action items, tasks, or next steps mentioned, extracted from the section summaries. For each task, if a person responsible was mentioned in the original section summary, include their name.

Ensure you include all sections even if some are empty (e.g., no tasks mentioned in any summary).
        """
    
    elif prompt_type == "chunk_summary":
        instruction = f"""
Summarize the following section of a meeting transcript concisely:
---
{content}
---
Concise Summary:
        """
    elif prompt_type == "single_full_summary_structured":
        instruction = f"""
Analyze the following meeting transcript, identify the main topic, provide a concise summary, extract key discussion points, and list any action items or tasks mentioned.

Transcript:
---
{content}
---

Provide the output in the following structure, using the exact markers provided:
[MAIN TOPIC]
A concise, overarching topic of the discussion.

[SUMMARY]
A brief summary of the entire conversation, highlighting the most important themes and outcomes.

[KEY POINTS]
- A bulleted list of the main discussion points, decisions made, or significant information shared.

[TASKS TO COMPLETE]
- A bulleted list of any action items, tasks, or next steps mentioned during the meeting. For each task, if a person responsible is mentioned or implied, include their name.

Ensure you include all sections even if some are empty (e.g., no tasks mentioned).
        """
    else:
        raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": instruction}
    ]
    
    if llm_tokenizer_instance is None:
        print("Error: LLM Tokenizer not loaded")
        return instruction
    
    prompt = llm_tokenizer_instance.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    return prompt


# --- Helper
# Run LLM Inference Async
async def generate_summary_async(prompt: str, max_new_tokens: int) -> str:
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
        "max_new_tokens": max_new_tokens, # Maximum number of tokens to generate (summary length)
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
    
    # Use find and slicing to extract content between markers
    text_after_main_topic = ""
    main_topic_start_marker_pos = llm_output_text.find("[MAIN TOPIC]")

    if main_topic_start_marker_pos != -1:
        main_topic_content_start = main_topic_start_marker_pos + len("[MAIN TOPIC]")

        summary_start_marker_pos = llm_output_text.find("[SUMMARY]", main_topic_content_start)
        main_topic_content_end = summary_start_marker_pos if summary_start_marker_pos != -1 else len(llm_output_text)
        parsed_data["main_topic"] = llm_output_text[main_topic_content_start:main_topic_content_end].strip()
        text_after_main_topic = llm_output_text[main_topic_content_end:] # Remaining text after main topic content


    text_after_summary = ""
    summary_start_marker_pos = text_after_main_topic.find("[SUMMARY]") if text_after_main_topic else llm_output_text.find("[SUMMARY]")
    if summary_start_marker_pos != -1:
         summary_start_abs_pos = (llm_output_text.find("[MAIN TOPIC]") + len("[MAIN TOPIC]") if llm_output_text.find("[MAIN TOPIC]") != -1 else 0) + summary_start_marker_pos if text_after_main_topic else summary_start_marker_pos
         summary_content_start = summary_start_abs_pos + len("[SUMMARY]")

         key_points_start_marker_pos = llm_output_text.find("[KEY POINTS]", summary_content_start)
         summary_content_end = key_points_start_marker_pos if key_points_start_marker_pos != -1 else len(llm_output_text)
         parsed_data["summary"] = llm_output_text[summary_content_start:summary_content_end].strip()
         text_after_summary = llm_output_text[summary_content_end:]


    key_points_start_marker_pos = text_after_summary.find("[KEY POINTS]") if text_after_summary else llm_output_text.find("[KEY POINTS]")
    if key_points_start_marker_pos != -1:
        key_points_start_abs_pos = (llm_output_text.find("[MAIN TOPIC]") + len("[MAIN TOPIC]") if llm_output_text.find("[MAIN TOPIC]") != -1 else 0) + (text_after_main_topic.find("[SUMMARY]") + len("[SUMMARY]") if text_after_main_topic.find("[SUMMARY]") != -1 else 0) + key_points_start_marker_pos if text_after_summary else key_points_start_marker_pos
        key_points_content_start = key_points_start_abs_pos + len("[KEY POINTS]")

        tasks_start_marker_pos = llm_output_text.find("[TASKS TO COMPLETE]", key_points_content_start)
        key_points_content_end = tasks_start_marker_pos if tasks_start_marker_pos != -1 else len(llm_output_text)
        key_points_block = llm_output_text[key_points_content_start:key_points_content_end].strip()

        # This regex splits the block by lines starting with '-' or '*' followed by whitespace
        key_point_items_with_markers = re.split(r'\n\s*[-\*]\s*', '\n' + key_points_block)
        # Clean up items: remove potential leading/trailing whitespace and empty items
        parsed_data["key_points"] = [item.strip() for item in key_point_items_with_markers if item.strip()]

    # Find start of tasks section (from the end of key points or where tasks marker was found)
    # Need a reliable way to find the start position if previous markers were missing.
    # Let's search from the beginning of the text for the marker.
    tasks_start_marker_pos = llm_output_text.find("[TASKS TO COMPLETE]")
    if tasks_start_marker_pos != -1:
         tasks_content_start = tasks_start_marker_pos + len("[TASKS TO COMPLETE]")
         tasks_block = llm_output_text[tasks_content_start:].strip() 
         
         # Split block into list items (look for lines starting with '-' or '*' followed by space/text)
         tasks_items_with_markers = re.split(r'\n\s*[-\*]\s*', '\n' + tasks_block)
         parsed_data["tasks_to_complete"] = [item.strip() for item in tasks_items_with_markers if item.strip()]
         

    print("LLM output parsing complete.")
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
    
    SINGLE_PASS_CHUNK_SIZE = 90000
    
    if len(transcript_text) <= SINGLE_PASS_CHUNK_SIZE:
    
        # Step 2: Define the prompt
        llm_prompt = get_llm_prompt("single_full_summary_structured", transcript_text)
        
        # Step 3: Run LLM Async
        llm_generated_text = await generate_summary_async(llm_prompt, 500)
        
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
    
    else: 
        # Chunked Summarization
        
        # Step 1: Chunk text
        print("Splitting text into chunks...")
        text_chunks = chunk_text_with_overlap(transcript_text)
        
        chunk_summaries_list = []
        
        # Step 2: Summarize each chunk
        for i, chunk_text in enumerate(text_chunks):
            
            chunk_prompt = get_llm_prompt("chunk_summary", chunk_text)
            
            chunk_summary_text = await generate_summary_async(chunk_prompt, 200)
            
            if chunk_summary_text.startswith("Error during") or not chunk_summary_text.strip():
                print("Error or empty summary...Skipping")
                continue
            
            chunk_summaries_list.append(f"Summary of Section {i+1}:\n{chunk_summary_text.strip()}")
            
        if not chunk_summaries_list:
            print("No chunk summaries generated")
            return {
                 "error": "No successful chunk summaries generated.",
                 "main_topic": "Summarization Failed",
                 "summary": "The chunked summarization process failed to produce any valid section summaries.",
                 "key_points": [],
                 "tasks_to_complete": []
            }
            
        # Step 3: Combine the chunk summaries into a single text
        combined_chunk_summaries_text = "\n\n---\n\n".join(chunk_summaries_list)
        print(f"Combined chunk summaries length: {len(combined_chunk_summaries_text)} characters.")
        
        # Step 4: Run LLM to combine Summaries
        print("Starting final summarization...")
        final_summary_prompt = get_llm_prompt("final_structured_summary", combined_chunk_summaries_text)
        
        
        llm_generated_text_final = await generate_summary_async(final_summary_prompt, 2000)
        
        if llm_generated_text_final.startswith("Error during"):
            print(f"LLM Generation Failed: {llm_generated_text_final}")
            return {
                "error": llm_generated_text_final, 
                "main_topic": "Summarization Failed", 
                "summary": llm_generated_text_final, 
                "key_points": [], 
                "tasks_to_complete": []
            }
            
        # Step 5: Parse LLM Output
        try:
            structured_summary_final = parse_llm_output(llm_generated_text_final)
            print("Chunked summarization process Succesful")
            return structured_summary_final
        except Exception as e:
            print(f"Error parsing LLM output from final summary pass: {e}")
            return {
                "error": f"Failed to parse final LLM output: {e}",
                "main_topic": "Parsing Failed",
                "summary": "Failed to parse the final summary from the LLM output.",
                "key_points": [],
                "tasks_to_complete": [],
                "raw_llm_output": llm_generated_text_final
            }
