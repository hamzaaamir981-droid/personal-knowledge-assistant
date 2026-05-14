import requests


response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3:8b",
        "prompt": "Explain Retrieval-Augmented Generation in one short sentence.",
        "stream": False
    }
)

data = response.json()

print(data["response"])