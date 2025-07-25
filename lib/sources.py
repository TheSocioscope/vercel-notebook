import json
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi

class Sources:
    def __init__(self):
        self.sources = []

    def append(self, source):
        self.sources.append(source)

    def remove(self, source):
        self.sources.remove(source)
    
    def __len__(self):
        return len(self.sources)

    def __iter__(self):
        return iter(self.sources)

    def __str__(self):
        return str(self.sources)
    
    def __repr__(self):
        return str(self.sources)

def load_transcripts(database, collection):
    # Connect to database
    uri = os.getenv('MONGODB_URI')
    client = MongoClient(uri, server_api=ServerApi('1'))

    try:
        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        # print("> MongoDB connected.")
        collection = client[database][collection]
        documents = [doc for doc in collection.find()]
        if len(documents)>0:
            return documents
        else:
            raise Exception('Collection is empty ! -> Load local samples')

    except Exception as e:
        print(e)

        # Load samples file
        with open('data/samples.json', 'r') as f:
            return json.load(f)

def build_navigation(transcripts):
    transcript_nav = {}
    for transcript in transcripts:
        country = transcript['COUNTRY']
        project = transcript['PROJECT'] + " - " + str(transcript['NAME'])
        record = transcript['FILE'][:-4]

        if country not in transcript_nav.keys():
            transcript_nav[country] = {}
        if project not in transcript_nav[country].keys():
            transcript_nav[country][project] = []
        if record not in transcript_nav[country][project]:
            transcript_nav[country][project].append(record)
    
    # Sort by country
    transcript_nav = {k: transcript_nav[k] for k in sorted(transcript_nav)}
    return transcript_nav

def build_rag_docs(transcripts):
    docs = {}
    for transcript in transcripts:
        key = transcript['FILE'][:-4]
        page_content = transcript['TRANSCRIPT']
        metadata = {k:v for k,v in transcript.items() if k not in ['TRANSCRIPT', '_id']}
        docs[key] = {'page_content':page_content, 'metadata':metadata}
    return docs