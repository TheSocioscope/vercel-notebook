import requests
import json
import os

RAG_API_ENPOINT = os.getenv('RAG_API_ENDPOINT')
RAG_API_KEY = os.getenv('RAG_API_KEY')
RAG_API_SECRET = os.getenv('RAG_API_SECRET')

class Message:
    order:int
    model:str
    question:str
    contents:list
    responses:list
    final_response:str
    
def send_rag(docs, message, model="openai:gpt-5-nano"):
    response = requests.post(
        url=RAG_API_ENPOINT,
        json={"docs":docs, "message":message, "model":model}),
        headers={"Modal-Key": RAG_API_KEY, "Modal-Secret": RAG_API_SECRET}
    return response.json()
    
