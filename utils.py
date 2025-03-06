import os
import wave
import time
import webrtcvad
import sounddevice as sd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import keyboard

CONFIG = {
    'OPTIMIZATION': {
        'vad_aggressiveness': 2,
        'max_silence': 1
    },
    'SAFETY': {
        'allowed_paths': ['~/']
    }
}

def transcribe(filename="command.wav"):
    # Add audio validation
    if not Path(filename).exists():
        raise FileNotFoundError(f"Audio file {filename} not found")
    

def record_until_silence(filename="command.wav"):
    """Manual recording with escape key"""
    RATE = 16000
    print("Press SPACE to stop recording...")
    
    with wave.open(filename, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        
        with sd.InputStream(samplerate=RATE, channels=1, dtype='int16') as stream:
            while True:
                audio, _ = stream.read(RATE)  # 1 second chunks
                f.writeframes(audio)
                
                # Check for space key press
                if keyboard.is_pressed('space'):
                    break

def validate_path(path):
    """Ensure paths stay within allowed directories"""
    resolved = Path(path).expanduser().resolve()
    allowed = [Path(p).expanduser() for p in CONFIG['SAFETY']['allowed_paths']]
    if not any(resolved.is_relative_to(a) for a in allowed):
        raise PermissionError(f"Access to {resolved} not permitted")
    return resolved