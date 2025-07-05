import json
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi

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

class Auth:
    def __init__(self):
        self.id = ''
        self.secret = ''
    
    def login(self, id, secret):
        self.id = id
        self.secret = secret

    def logout(self):
        self.id = ''
        self.secret = ''

    def authenticate(self):
        return (( self.id == os.getenv("AUTH_ID")) 
                and (self.secret == os.getenv("AUTH_SECRET"))) 