import json
import os

def load_transcripts(data_path):
    with open(data_path, 'r') as f:
        return json.load(f)

def make_transcript_nav(transcripts):
    transcript_nav = {}
    for transcript in transcripts:
        country = transcript['metadata']['COUNTRY']
        project = transcript['metadata']['PROJECT'] + " - " + str(transcript['metadata']['NAME'])
        record = transcript['metadata']['FILE'][:-4]

        if country not in transcript_nav.keys():
            transcript_nav[country] = {}
        if project not in transcript_nav[country].keys():
            transcript_nav[country][project] = []
        if record not in transcript_nav[country][project]:
            transcript_nav[country][project].append(record)
    
    # Sort by country
    transcript_nav = {k: transcript_nav[k] for k in sorted(transcript_nav)}

    return transcript_nav

def authentication(login):
    return ((login[0] == os.getenv("AUTH_ID")) 
            and (login[1] == os.getenv("AUTH_SECRET"))) 