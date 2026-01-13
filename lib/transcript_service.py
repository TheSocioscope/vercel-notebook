from lib.sources import get_transcripts_content_async, parse_transcript, get_unique_speakers
from config import DB_NAME, COLLECTION_NAME


# Transcript content cache (LRU-style)
_TRANSCRIPT_CACHE_MAX = 8
_transcript_cache: dict[str, dict] = {}
_transcript_cache_order: list[str] = []


def _cache_get(filename: str):
    if filename not in _transcript_cache:
        return None
    # refresh LRU-ish order
    try:
        _transcript_cache_order.remove(filename)
    except ValueError:
        pass
    _transcript_cache_order.append(filename)
    return _transcript_cache[filename]


def _cache_set(filename: str, value: dict):
    if filename in _transcript_cache:
        _transcript_cache[filename] = value
        try:
            _transcript_cache_order.remove(filename)
        except ValueError:
            pass
        _transcript_cache_order.append(filename)
        return

    _transcript_cache[filename] = value
    _transcript_cache_order.append(filename)
    while len(_transcript_cache_order) > _TRANSCRIPT_CACHE_MAX:
        evict = _transcript_cache_order.pop(0)
        _transcript_cache.pop(evict, None)


async def get_parsed_transcript(filename: str):
    """
    Fetch and parse a transcript, with LRU caching.
    Returns dict with 'metadata', 'segments', and 'speakers' keys, or None if not found.
    """
    cached = _cache_get(filename)
    if cached:
        return cached

    contents = await get_transcripts_content_async(DB_NAME, COLLECTION_NAME, [filename])
    if filename not in contents:
        return None

    transcript_text = contents[filename]
    metadata = {"NAME": filename}

    segments = parse_transcript(transcript_text)
    speakers = get_unique_speakers(segments)

    payload = {"metadata": metadata, "segments": segments, "speakers": speakers}
    _cache_set(filename, payload)
    return payload
