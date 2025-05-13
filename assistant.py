#Operator/assistant.py
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
from pydub import AudioSegment
import json
import time

from executor import execute_action
from llama_cpp import Llama

# -------------------------------------------------------------------
# 1. GLOBAL SETUP
# -------------------------------------------------------------------

# Path to your LLaMA-based model. Adjust as necessary.
MODEL_PATH = "./llama.cpp/models/Mistral-7B-Instruct-v0.3.Q4_K_M.gguf"

# You can tweak these parameters to find the right speed vs. quality tradeoff.
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=512,      # smaller context speeds up inference for short commands
    n_threads=8,
    n_gpu_layers=999,  # (Uncomment if you want partial GPU acceleration on Apple Silicon)
    n_batch=256       # (Helps performance for short queries in many cases)
)

SYSTEM_PROMPT = """Convert user commands into a JSON object with the form:

{
  "action": "<script_name>",
  "params": {
    "key": "value",
    ...
  }
}
Available actions (scripts): delete_file, move_file, create_folder, open_file, search_files.
Example: "move/delete test.txt to Trash/Recycle Bin/Garbage":
Output: {"action": "delete_file", "params": {"path": "~/Desktop/test.txt"}}

Example: "Move report.pdf from Downloads to Documents":
Output: {"action": "move_file", "params": {"source": "~/Downloads/report.pdf", "destination": "~/Documents"}}
"""


def record_voice(filename="command.wav", duration=3):
    """
    Records audio from the system microphone for `duration` seconds.
    Make sure you have SoX installed (brew install sox).
    """
    print(f"Recording {duration} second(s) of audio... speak now.")
    os.system(f"sox -d -r 16000 -c 1 {filename} trim 0 {duration}")

def transcribe_audio():
    """
    Uses whisper.cpp to transcribe the recorded audio into text.
    """
    if not os.path.exists("command.wav"):
        raise FileNotFoundError("Record audio first using record_voice()")
    
    try:
        # Convert audio to 16kHz, mono, 16-bit PCM

        #blah blah git check
        sound = AudioSegment.from_file("command.wav")
        sound = (sound.set_frame_rate(16000)
                      .set_channels(1)
                      .set_sample_width(2))
        sound.export("command_16k.wav", format="wav", codec="pcm_s16le")
        
        # Paths
        whisper_cli_path = os.path.abspath("whisper.cpp/build/bin/whisper-cli")
        # You can speed up transcription by switching to "ggml-tiny.en.bin" or "ggml-small.en.bin"
        # if you have them downloaded in the models folder.
        model_path = os.path.abspath("whisper.cpp/models/ggml-base.en.bin")
        audio_path = os.path.abspath("command_16k.wav")
        
        # Run whisper.cpp CLI with multi-threading (-t 8)
        print("Transcribing audio with whisper.cpp (this may take a few seconds)...")
        result = subprocess.run([
            whisper_cli_path,
            "-m", model_path,
            "-f", audio_path,
            "-otxt",
            "-l", "en",
            "-t", "8"
        ], capture_output=True, text=True)
        
        if result.stderr:
            print("Whisper CLI stderr:", result.stderr)
        
        txt_path = audio_path + ".txt"
        if not os.path.exists(txt_path):
            raise FileNotFoundError(f"Missing Whisper output file: {txt_path}")
        
        with open(txt_path, "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Transcription failed: {str(e)}")
        return ""

def process_command(text):
    """
    Feeds the user's text command into the LLM with a system prompt, 
    expecting a JSON output specifying {"action": "...", "params": {...}}.
    """
    prompt = f"{SYSTEM_PROMPT}\n\nUser: {text}\nAssistant:"
    print("Sending to LLM:", prompt)
    
    # You can experiment with smaller max_tokens if you prefer.
    output = llm(prompt, max_tokens=128, temperature=0.2, stop=["\n"], echo=False)
    
    # LLM output (the raw text after "Assistant:")
    json_str = output["choices"][0]["text"].strip()

    print("LLM Raw Output:", output)
    print("Attempted JSON:", json_str)

    # Validate JSON
    try:
        # Just to ensure it's valid JSON. We'll pass the raw string forward to executor.
        _ = json.loads(json_str)
        return json_str
    except json.JSONDecodeError:
        print(f"Invalid JSON from LLM: {json_str}")
        return ""

def main_loop():
    """
    Repeatedly record, transcribe, process with LLM, and execute until user quits.
    """
    while True:
        choice = input("Type 'v' for voice, 't' for text, or 'q' to quit: ").strip().lower()
        if choice == 'q':
            print("Exiting...")
            break
        elif choice == 'v':
            record_voice()
            text_command = transcribe_audio()
            print("Transcription:", text_command)
        elif choice == 't':
            text_command = input("Enter your command: ").strip()
            print("Text input:", text_command)
        else:
            print("Invalid choice. Try again.")
            continue
        
        json_output = process_command(text_command)
            
        # 4. Execute
        if json_output:
            execute_action(json_output)


if __name__ == "__main__":
    main_loop()

