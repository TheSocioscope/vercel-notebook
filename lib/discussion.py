import requests
import json
import os

RAG_API_ENPOINT = os.getenv('RAG_API_ENDPOINT')

class Message:
    order:int
    model:str
    question:str
    contents:list
    responses:list
    final_response:str
    
def send_rag(docs, message, model="openai:gpt-4o-mini"):
    response = requests.post(
        url=RAG_API_ENPOINT,
        json={"docs":docs, "message":message, "model":model})
    return response.json()
    
