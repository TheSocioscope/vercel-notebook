import json
import os
import re
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from motor.motor_asyncio import AsyncIOMotorClient


class Source:
    filename: str
    page_content: str
    metadata: dict


# Reusable async MongoDB client (connection pooling handled by Motor)
_motor_client = None


def _get_motor_client():
    """Get or create a reusable Motor client."""
    global _motor_client
    if _motor_client is None:
        uri = os.getenv("MONGODB_URI")
        _motor_client = AsyncIOMotorClient(uri)
    return _motor_client


async def load_transcripts_metadata_async(database: str, collection: str):
    """
    Async function to load transcript metadata only (excludes TRANSCRIPT field).
    This is fast because we don't transfer the large text content.
    """
    try:
        client = _get_motor_client()
        coll = client[database][collection]
        
        # Exclude TRANSCRIPT field for fast metadata-only fetch
        cursor = coll.find({}, {"TRANSCRIPT": 0})
        documents = await cursor.to_list(length=None)
        
        if documents:
            return documents
        else:
            raise Exception("Collection is empty! -> Load local samples")
            
    except Exception as e:
        print(f"LOG:\tAsync load failed: {e}")
        # Fallback to local samples
        with open("data/samples.json", "r") as f:
            samples = json.load(f)
            # Return without TRANSCRIPT to match the expected structure
            return [{k: v for k, v in doc.items() if k != "TRANSCRIPT"} for doc in samples]


async def get_transcripts_content_async(database: str, collection: str, filenames: list[str]):
    """
    Async function to fetch full transcript content for specific files only.
    This enables lazy loading - only fetch what the user needs for RAG.
    
    Args:
        filenames: List of filenames WITHOUT extension (e.g., ["CO-006_interview_audio"])
    
    Returns: dict mapping filename (without extension) -> transcript content
    """
    try:
        client = _get_motor_client()
        coll = client[database][collection]
        
        # Query where FILE starts with any of the filenames followed by a dot
        # This handles any extension (.txt, .m4a, .MP4, etc.)
        # Build regex pattern: ^(filename1\.|filename2\.|filename3\.)
        if not filenames:
            return {}
        
        escaped_filenames = [re.escape(fn) for fn in filenames]
        regex_pattern = f"^({'|'.join(escaped_filenames)})\\."
        
        cursor = coll.find(
            {"FILE": {"$regex": regex_pattern}},
            {"FILE": 1, "TRANSCRIPT": 1}
        )
        documents = await cursor.to_list(length=None)
        
        # Return as dict: filename (without extension) -> content
        result = {}
        for doc in documents:
            file_with_ext = doc["FILE"]
            # Extract filename without extension (last 4 chars are extension)
            filename_no_ext = file_with_ext[:-4] if len(file_with_ext) > 4 else file_with_ext
            if filename_no_ext in filenames:
                result[filename_no_ext] = doc.get("TRANSCRIPT", "")
        
        return result
        
    except Exception as e:
        print(f"LOG:\tFailed to fetch transcript content: {e}")
        # Fallback to local samples
        with open("data/samples.json", "r") as f:
            samples = json.load(f)
            return {
                doc["FILE"][:-4]: doc.get("TRANSCRIPT", "")
                for doc in samples
                if doc["FILE"][:-4] in filenames
            }


# Keep synchronous version for local development/fallback
def load_transcripts(database, collection):
    """Synchronous version - used as fallback."""
    uri = os.getenv("MONGODB_URI")
    client = MongoClient(uri, server_api=ServerApi("1"))

    try:
        client.admin.command("ping")
        collection = client[database][collection]
        documents = [doc for doc in collection.find()]
        if len(documents) > 0:
            return documents
        else:
            raise Exception("Collection is empty ! -> Load local samples")

    except Exception as e:
        print(e)
        with open("data/samples.json", "r") as f:
            return json.load(f)


def build_navigation(transcripts):
    """Build navigation tree from transcript metadata."""
    transcript_nav = {}
    for transcript in transcripts:
        country = transcript["COUNTRY"]
        project = transcript["PROJECT"] + " - " + str(transcript["NAME"])
        record = transcript["FILE"][:-4]

        if country not in transcript_nav.keys():
            transcript_nav[country] = {}

        if project not in transcript_nav[country].keys():
            transcript_nav[country][project] = []

        if record not in transcript_nav[country][project]:
            transcript_nav[country][project].append(record)
            transcript_nav[country][project] = sorted(transcript_nav[country][project])

    # Sort by country
    transcript_nav = {k: transcript_nav[k] for k in sorted(transcript_nav)}
    return transcript_nav
