CONFIG = {
    'OPTIMIZATION': {
        'llm_threads': 4,  # Reduced from 8 for stability
        'audio_threads': 2,
        'gpu_layers': 1,  # Start with 1 layer for testing
        'vad_aggressiveness': 2,
        'max_silence': 1.0
    },
    'PATHS': {
        'scripts': 'scripts',
        'models': 'llama.cpp/models',
        'memory_db': 'memory/history.db',
        'whisper_cli': 'whisper.cpp/build/bin/whisper-cli',
        'whisper_model': 'whisper.cpp/models/ggml-base.en.bin'  # New path

    },
    'SAFETY': {
        'allowed_paths': ['Desktop', 'Documents'],
        'confirm_destructive': True
    },
    'PERSONALITY': {
        'voice_rate': 180,
        'voice_id': 'com.apple.speech.synthesis.voice.Alex',
        'system_prompt': """You are JARVIS, an AI assistant. Respond technically but concisely.
        Available commands: delete_file, move_file, create_folder, open_file, search_files
        Examples:
        - "Delete test.txt from Desktop" => {"action":"delete_file","params":{"path":"~/Desktop/test.txt"}}
        - "Move report.pdf to Documents" => {"action":"move_file","params":{"source":"~/Downloads/report.pdf","destination":"~/Documents"}}"""
    }
}