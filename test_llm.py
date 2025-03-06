from assistant import process_command, SYSTEM_PROMPT
from llama_cpp import Llama

llm = Llama(
    model_path="./llama.cpp/models/Mistral-7B-Instruct-v0.3.Q4_K_M.gguf",
    n_ctx=2048,
    n_threads=8
)

test_cases = [
    "Delete report.pdf from Downloads",
    "Move presentation.pptx from Desktop to Documents",
    "Create new folder called Projects in home directory"
]

for cmd in test_cases:
    print(f"Command: {cmd}")
    print("JSON Output:", process_command(cmd))
    print("-" * 40)