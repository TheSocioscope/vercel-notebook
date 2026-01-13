import os
import json
from fastlite import *
from fasthtml.svg import *
from fasthtml.common import *
from monsterui.all import *
from lib.discussion import send_rag
from lib.sources import *
from lib.transcript_service import get_parsed_transcript
from lib.auth import generate_magic_link, verify_token, is_email_allowed, MagicLinkRequest
from styles import css

# Import UI components
from components import (
    render_response,
    PromptForm,
    TranscriptsCard,
    TranscriptSegmentRow,
    TranscriptLoadingSkeleton,
    TranscriptLoadMoreSentinel,
    TranscriptViewer,
    LoginPage,
    AppPage,
)

# Import configuration and database from config.py
from config import (
    SESSION_SECRET,
    IS_PRODUCTION,
    DB_NAME,
    COLLECTION_NAME,
    MAX_SESSION_AGE,
    sources,
)

# Client-side JavaScript for transcript selection
selection_js = Script("""
function updateSourcesList() {
    // LabelCheckboxX creates checkboxes, find them by looking for inputs within transcript-checkbox-wrapper
    const wrappers = document.querySelectorAll('.transcript-checkbox-wrapper');
    const checkboxes = Array.from(wrappers)
        .map(w => w.querySelector('input[type="checkbox"]'))
        .filter(cb => cb && cb.checked);
    const selectedInput = document.getElementById('selected-transcripts');
    const selected = checkboxes.map(cb => cb.value || cb.id);
    if (selectedInput) {
        selectedInput.value = selected.join(',');
    }
}
""")
hdrs = (Theme.neutral.headers(apex_charts=True, highlightjs=True, daisy=True), css, selection_js)

# Create your app with the theme and secure session config
app, rt = fast_app(
    hdrs=hdrs,
    live=not IS_PRODUCTION,
    secret_key=SESSION_SECRET,
    sess_cookie="socioscope_session",
    max_age=MAX_SESSION_AGE,
    sess_https_only=IS_PRODUCTION,  # HTTPS-only in production
    same_site="lax",
)


@rt("/ask")
async def ask(query: str, selected: str = ""):
    """Handle RAG query - synchronous, serverless-friendly."""
    # Get selected transcript filenames from client-side selection
    selected_filenames = [s.strip() for s in selected.split(",") if s.strip()]

    if not selected_filenames:
        return Div(cls="uk-card-secondary p-4")(
            "Please select at least one source in the transcripts panel."
        )

    # Fetch transcript content on-demand for selected files
    print(f"LOG:\tFetching content for {len(selected_filenames)} selected transcripts...")
    content_map = await get_transcripts_content_async(DB_NAME, COLLECTION_NAME, selected_filenames)

    if not content_map:
        return Div(cls="uk-card-secondary p-4")(
            "Failed to load transcript content. Please try again."
        )

    # Build docs for RAG (we need page_content and metadata)
    docs = []
    for filename in selected_filenames:
        if filename in content_map:
            content = content_map[filename]
            # Try to get metadata from cache, fallback to basic metadata
            try:
                cached = sources[filename]
                metadata = json.loads(cached.metadata)
            except (NotFoundError, Exception):
                metadata = {"filename": filename}

            docs.append(dict(page_content=content, metadata=metadata))

    if not docs:
        return Div(cls="uk-card-secondary p-4")(
            "Selected transcripts not found. Please try again."
        )

    # Call RAG synchronously - wait for response (serverless-friendly)
    print(f'LOG:\tSending "{query[:50]}..." for RAG on {len(docs)} documents...')
    try:
        response = send_rag(docs=docs, message=query)
        return render_response(response["final_response"])
    except Exception as e:
        print(f"LOG:\tRAG error: {e}")
        return Div(cls="uk-card-secondary p-4")(
            "Sorry, there was an error processing your request. Please try again."
        )


@rt("/load-transcripts")
async def load_transcripts_route():
    """
    Async endpoint to load transcripts from MongoDB.
    Called via HTMX after initial page render.
    This decouples the slow database fetch from the initial page load.
    """
    print("LOG:\tLoading transcripts asynchronously...")

    # Fetch metadata only (no TRANSCRIPT content) - this is fast!
    transcripts_metadata = await load_transcripts_metadata_async(DB_NAME, COLLECTION_NAME)

    print(f"LOG:\tLoaded {len(transcripts_metadata)} transcript metadata entries")

    # Cache metadata in sources table (without content - content loaded on-demand in ask())
    for transcript in transcripts_metadata:
        filename = transcript["FILE"][:-4]
        try:
            sources[filename]
        except NotFoundError:
            sources.insert(
                Source(
                    filename=filename,
                    page_content="",  # Content loaded lazily when needed for RAG
                    metadata={
                        k: str(v)
                        for k, v in transcript.items()
                        if k not in ["TRANSCRIPT", "_id"]
                    },
                )
            )

    # Build navigation tree
    transcript_nav = build_navigation(transcripts_metadata)

    return TranscriptsCard(transcript_nav, len(transcripts_metadata))


@rt("/read-transcript")
async def read_transcript_shell(filename: str):
    """
    Fast endpoint: immediately returns a skeleton, then HTMX loads the transcript content.
    This keeps the tab switch and initial render instant even for very long transcripts.
    """
    # Important: keep the skeleton *inside* the element that will be swapped,
    # otherwise the skeleton would remain visible even after content loads.
    return Div(
        id="transcript-content-loader",
        hx_get=f"/read-transcript-content?filename={filename}&offset=0&limit=200",
        hx_trigger="load",
        hx_swap="outerHTML",
        cls="p-4",
    )(TranscriptLoadingSkeleton())


@rt("/read-transcript-content")
async def read_transcript_content(filename: str, offset: int = 0, limit: int = 200):
    data = await get_parsed_transcript(filename)
    if not data:
        return Div(cls="p-4 text-center")(P("Transcript not found.", cls="text-red-400"))

    return TranscriptViewer(
        metadata=data["metadata"],
        segments=data["segments"],
        speakers=data["speakers"],
        offset=offset,
        limit=limit,
        filename=filename,
    )


@rt("/read-transcript-chunk")
async def read_transcript_chunk(filename: str, offset: int = 200, limit: int = 200):
    data = await get_parsed_transcript(filename)
    if not data:
        return Div()

    segments = data["segments"]
    speakers = data["speakers"]
    total = len(segments)
    chunk = segments[offset: offset + limit]

    return Div(
        *[TranscriptSegmentRow(seg) for seg in chunk],
        TranscriptLoadMoreSentinel(filename, offset + limit, limit) if (offset + limit) < total else None,
    )


@rt
def index(session):
    """Main app - requires login."""
    if session.get("email"):
        return (Title("Socioscope"), AppPage)
    return RedirectResponse(url="/auth")


@rt("/auth")
def get(session, token: str = None):
    """Handle GET /auth - show login form or verify magic link token."""
    # If already logged in, go to app
    if session.get("email"):
        return RedirectResponse(url="/")

    # If token provided, verify it
    if token:
        success, result = verify_token(token)
        if success:
            session["email"] = result  # Store email in session cookie
            print(f"LOG:\tUser logged in: {result}")
            return RedirectResponse(url="/")
        else:
            return (Title("Socioscope"), LoginPage(message=f"❌ {result}"))

    # No token, show login form
    return (Title("Socioscope"), LoginPage())


@rt("/auth")
def post(req: MagicLinkRequest, request):
    """Handle POST /auth - generate and print magic link."""
    is_htmx = request.headers.get("HX-Request") == "true"

    if not is_email_allowed(req.email):
        if is_htmx:
            return P("❌ Email domain not authorized.")
        return (Title("Socioscope"), LoginPage(message="❌ Email domain not authorized."))

    base_url = os.getenv("BASE_URL", "http://localhost:5001")
    generate_magic_link(req.email, base_url=base_url)

    if is_htmx:
        return P("✅ Magic link sent! Check your email.")
    return (Title("Socioscope"), LoginPage(message=f"✅ Magic link sent! Check your email."))


# For local development
if __name__ == "__main__":
    serve()

# For Vercel deployment - export the ASGI application
application = app
