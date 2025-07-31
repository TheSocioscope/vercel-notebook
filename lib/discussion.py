import requests
import json
import os

RAG_API_ENPOINT = os.getenv('RAG_API_ENDPOINT')

class Message:
    order:int
    query:str
    context:list
    model:str 
    response:str
    
def send_rag(docs, message, model="openai:gpt-4o-mini"):
    response = requests.post(
        url=RAG_API_ENPOINT,
        json={"docs":docs, "message":message, "model":model})
    return response.json()
    
