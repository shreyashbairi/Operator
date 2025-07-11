# #Operator/assistant.py

# This script is the main interface for the voice assistant. It records audio from
# the microphone, transcribes it, processes it with the LLaMA model, and executes
# the resulting action using the executor module. The main_loop function repeatedly
# records, transcribes, processes, and executes commands until the user quits. The
# record_voice function uses SoX to record audio from the system microphone. The
# transcribe_audio function uses whisper.cpp to transcribe the recorded audio into text.
# The process_command function feeds the user's text command into the LLaMA model with
# a system prompt, expecting a JSON output specifying {"action": "...", "params": {...}}.
# The main interface for the assistant is the main_loop function, which orchestrates the
# entire process. It records audio, transcribes it, processes it with LLaMA, and executes
# the resulting action until the user quits.
#

import os
import subprocess
import json
import time
from pydub import AudioSegment
from llama_cpp import Llama

from executor import execute_action

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

MODEL_PATH = "./llama.cpp/models/Mistral-7B-Instruct-v0.3.Q4_K_M.gguf"
WHISPER_MODEL = "ggml-base.en.bin"  # Options: ggml-tiny.en.bin, ggml-small.en.bin

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=512,
    n_threads=8,
    n_gpu_layers=999,
    n_batch=256
)

SYSTEM_PROMPT = """Convert user commands into JSON. Follow these rules STRICTLY:

1. For file operations, require FULL PATHS unless the user specifies a common location (e.g., "Desktop"). If path isn't specified, use "ASK_USER" as its value.
2. Always use tilde (~) for home directory paths (ex. for Desktop/Documents/etc., use ~/Desktop, ~/Documents, etc.)

Example: "Move my document.pdf"
Output: {"action": "move_file", "params": {"source": "~/Desktop/document.pdf", "destination": "ASK_USER"}}

Example: "Move document.pdf to Documents":
Output: {"action": "move_file", "params": {"source": "~/Desktop/document.pdf", "destination": "~/Documents"}}

Example: "move/delete test.txt to Trash/Recycle Bin/Garbage":
Output: {"action": "delete_file", "params": {"path": "~/Desktop/test.txt"}}

Example: "Create a folder called Backup"
Output: {"action": "create_folder", "params": {"path": "ASK_USER/Backup"}}

Process Management:
- "Show running apps" → {"action": "list_processes", "params": {}}
- "Quit Safari" → {"action": "kill_process", "params": {"target": "Safari"}}
- "Force quit/quit Notes" → {"action": "kill_process", "params": {"force": true, "target": "Notes"}}
- "lock my system" → {"action": "lock_system", "params": {}}
- "sleep" → {"action": "sleep", "params": {}}
"""
# ------------------------------------------------------------------------------
# Audio Processing
# ------------------------------------------------------------------------------

def record_voice(duration=3, filename="command.wav"):
    """Record audio from microphone using SoX"""
    print(f"Recording {duration} second(s)...")
    os.system(f"sox -d -r 16000 -c 1 {filename} trim 0 {duration}")

def convert_audio(input_file, output_file="command_16k.wav"):
    """Convert audio to 16kHz mono PCM format"""
    sound = AudioSegment.from_file(input_file)
    sound = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    sound.export(output_file, format="wav", codec="pcm_s16le")
    return output_file

def transcribe_audio(audio_file="command.wav"):
    """Transcribe audio using whisper.cpp"""
    if not os.path.exists(audio_file):
        raise FileNotFoundError("No audio file to transcribe")
    
    converted_file = convert_audio(audio_file)
    whisper_cli = os.path.abspath("whisper.cpp/build/bin/whisper-cli")
    model_path = os.path.abspath(f"whisper.cpp/models/{WHISPER_MODEL}")
    
    print("Transcribing audio...")
    result = subprocess.run([
        whisper_cli, "-m", model_path, "-f", converted_file,
        "-otxt", "-l", "en", "-t", "8"
    ], capture_output=True, text=True)
    
    if result.stderr:
        print("Whisper warnings:", result.stderr)
    
    txt_path = converted_file + ".txt"
    with open(txt_path, "r") as f:
        return f.read().strip()

# ------------------------------------------------------------------------------
# Command Processing
# ------------------------------------------------------------------------------

def process_command(user_input):
    """Transform natural language command into executable JSON"""
    prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_input}\nAssistant:"
    print(f"Processing: {user_input}")
    
    response = llm(prompt, max_tokens=128, temperature=0.2, stop=["\n"], echo=False)
    json_output = response["choices"][0]["text"].strip()
    
    # Log for training purposes
    with open("training_data.jsonl", "a") as f:
        f.write(json.dumps({"prompt": user_input, "completion": json_output}) + "\n")
    
    # Validate JSON format
    try:
        json.loads(json_output)  # Test validity
        return json_output
    except json.JSONDecodeError:
        print(f"Invalid JSON response: {json_output}")
        return ""

# ------------------------------------------------------------------------------
# Main Application Loop
# ------------------------------------------------------------------------------

def main_loop():
    """Main interaction loop for voice assistant"""
    print("Assistant ready. Press Ctrl+C to exit")
    
    while True:
        mode = input("\nChoose input method:\n[v] Voice\n[t] Text\n[q] Quit\n> ").lower()
        
        if mode == 'q':
            print("Exiting...")
            break
            
        if mode == 'v':
            record_voice()
            try:
                command = transcribe_audio()
                print(f"Transcribed: {command}")
            except Exception as e:
                print(f"Transcription error: {e}")
                continue
        elif mode == 't':
            command = input("Command: ")
        else:
            print("Invalid selection")
            continue
            
        if json_command := process_command(command):
            execute_action(json_command)

if __name__ == "__main__":
    main_loop()