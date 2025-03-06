import pyttsx3
from llama_cpp import Llama
from pathlib import Path
import json
from config import CONFIG

class JARVIS:
    def __init__(self):
        # Initialize TTS engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', CONFIG['PERSONALITY']['voice_rate'])
        self.engine.setProperty('voice', CONFIG['PERSONALITY']['voice_id'])
        
        # Initialize LLM
        model_path = Path(CONFIG['PATHS']['models']).expanduser()/"Mistral-7B-Instruct-v0.3.Q4_K_M.gguf"
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")
            
        self.llm = Llama(
            model_path=str(model_path),
            n_ctx=4096,  # Increased from 2048
            n_gpu_layers=CONFIG['OPTIMIZATION']['gpu_layers'],
            n_threads=CONFIG['OPTIMIZATION']['llm_threads'],
            use_mlock=False,
            mmap=True,
            logits_all=False  # Critical for Mistral models
        )
    
    def process_command(self, text):
        """Convert voice command to JSON using system prompt"""
        prompt = f"[INST] {CONFIG['PERSONALITY']['system_prompt']}\nConvert this command: {text} [/INST]"
        response = self.llm(
            prompt,
            max_tokens=150,
            temperature=0.1,
            stop=["\n", "}", "[/INST]"]
        )
        json_str = "{" + response['choices'][0]['text'].split("{", 1)[-1].strip()
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            self.respond("Failed to parse command")
            return None

    def respond(self, text):
        """Generate personality response"""
        prompt = f"[INST] {CONFIG['PERSONALITY']['system_prompt']}\nRespond to this outcome: {text} [/INST]"
        response = self.llm(
            prompt,
            max_tokens=50,
            temperature=0.3,
            stop=["\n", "[/INST]"]
        )
        message = response['choices'][0]['text'].strip()
        self.speak(message)
        return message
    
    def speak(self, text):
        """Direct TTS without LLM"""
        self.engine.say(text)
        self.engine.runAndWait()