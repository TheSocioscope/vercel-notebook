import requests
import json
import os

RAG_API_ENPOINT = os.getenv('RAG_API_ENDPOINT')

def rag(docs, message, model="openai:gpt-4o-mini"):
    response = requests.post(
        url=RAG_API_ENPOINT,
        json={"docs":docs, "message":message, "model":model}
    )
    return response.json()

class Messages:
    def __init__(self):
        self.messages = []

    def append(self, message):
        self.messages.append(message)

    def remove(self, message):
        self.messages.remove(message)
    
    def __len__(self):
        return len(self.messages)

    def __iter__(self):
        return iter(self.messages)

    def __str__(self):
        return str(self.messages)
    
    def __repr__(self):
        return str(self.messages)

