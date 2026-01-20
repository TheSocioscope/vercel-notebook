import os
from fasthtml.svg import *
from fasthtml.common import *
from monsterui.all import *
from lib.discussion import map_document, reduce_responses
from lib.sources import load_transcripts_metadata_async, get_transcripts_content_async, build_navigation
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

# Import configuration
from config import (
    SESSION_SECRET,
    IS_PRODUCTION,
    DB_NAME,
    COLLECTION_NAME,
    MAX_SESSION_AGE,
)

# Client-side JavaScript for transcript selection and RAG orchestration
selection_js = Script("""
function updateSourcesList() {
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

// Chat history management
const HISTORY_KEY = 'socioscope_chat_history';

function saveChat(query, response) {
    const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    history.unshift({
        id: Date.now(),
        query: query.substring(0, 100),
        fullQuery: query,
        response: response,
        timestamp: new Date().toISOString()
    });
    try {
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (e) {
        // localStorage full - remove oldest entries and retry
        console.warn('localStorage full, removing old entries');
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, Math.floor(history.length / 2))));
    }
    renderHistoryList();
}

function renderHistoryList() {
    const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    const container = document.getElementById('history-list');
    if (!container) return;
    
    if (history.length === 0) {
        container.innerHTML = '<p class="text-center opacity-50 p-8">No chat history yet</p>';
        return;
    }
    
    container.innerHTML = history.map(chat => `
        <div class="history-item p-3 border-b border-[hsl(var(--border))] cursor-pointer hover:bg-[hsl(var(--background))] transition-colors" 
             onclick="loadChat(${chat.id})">
            <p class="text-xs opacity-50">${new Date(chat.timestamp).toLocaleString()}</p>
            <p class="text-sm truncate mt-1 opacity-80">${chat.query}${chat.query.length >= 100 ? '...' : ''}</p>
        </div>
    `).join('');
}

function loadChat(id) {
    const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    const chat = history.find(h => h.id === id);
    if (chat) {
        document.getElementById('query').value = chat.fullQuery;
        document.getElementById('discussion-results').innerHTML = chat.response;
        document.getElementById('discussion-tab').click();
        if (window.UIkit) {
            UIkit.update(document.getElementById('discussion-results'));
        }
    }
}

function clearHistory() {
    if (confirm('Clear all chat history?')) {
        localStorage.removeItem(HISTORY_KEY);
        renderHistoryList();
    }
}

document.addEventListener('DOMContentLoaded', renderHistoryList);

// Client-side RAG orchestration - parallel map, then reduce
async function executeRAG(event) {
    event.preventDefault();
    
    const form = event.target;
    const query = form.querySelector('#query').value;
    const selected = form.querySelector('#selected-transcripts').value;
    const resultsDiv = document.getElementById('discussion-results');
    const progressDiv = document.getElementById('rag-progress');
    
    if (!selected) {
        resultsDiv.innerHTML = '<div class="uk-card-secondary p-4">Please select at least one source in the transcripts panel.</div>';
        return;
    }
    
    const filenames = selected.split(',').filter(s => s.trim());
    const total = filenames.length;
    
    // Show progress UI
    progressDiv.style.display = 'flex';
    progressDiv.innerHTML = `
        <div class="animate-spin rounded-full h-10 w-10 border-4 border-primary border-t-transparent"></div>
        <div class="text-center">
            <p class="text-sm opacity-70">Processing documents...</p>
            <p class="text-xs opacity-50 mt-1" id="progress-text">0 / ${total} documents</p>
            <div class="w-48 h-2 bg-muted rounded-full mt-2 overflow-hidden">
                <div id="progress-bar" class="h-full bg-primary transition-all duration-300" style="width: 0%"></div>
            </div>
        </div>
    `;
    resultsDiv.innerHTML = '';
    
    try {
        // Phase 1: Map - process all documents in parallel
        let completed = 0;
        const mapPromises = filenames.map(async (filename) => {
            const response = await fetch('/map', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ query, filename })
            });
            const result = await response.json();
            completed++;
            document.getElementById('progress-text').textContent = `${completed} / ${total} documents`;
            document.getElementById('progress-bar').style.width = `${(completed / total) * 80}%`;
            return result;
        });
        
        const mapResults = await Promise.all(mapPromises);
        
        // Check for errors
        const errors = mapResults.filter(r => r.error);
        if (errors.length === mapResults.length) {
            throw new Error('All document processing failed');
        }
        
        const responses = mapResults.filter(r => !r.error).map(r => r.response);
        
        // Phase 2: Reduce - consolidate responses
        document.getElementById('progress-text').textContent = 'Consolidating responses...';
        document.getElementById('progress-bar').style.width = '90%';
        
        const reduceResponse = await fetch('/reduce', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'HX-Request': 'true'  // Tell FastHTML to return fragment only
            },
            body: JSON.stringify({ query, responses })
        });
        
        const finalResult = await reduceResponse.text();
        
        // Done - show results
        document.getElementById('progress-bar').style.width = '100%';
        progressDiv.style.display = 'none';
        resultsDiv.innerHTML = finalResult;
        
        // Re-initialize UIkit components only in the new content, not the whole page
        if (window.UIkit) {
            UIkit.update(resultsDiv);
        }
        
        // Save to chat history
        saveChat(query, finalResult);
        
    } catch (error) {
        progressDiv.style.display = 'none';
        resultsDiv.innerHTML = `<div class="uk-card-secondary p-4">Error: ${error.message}. Please try again.</div>`;
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


@rt("/map")
async def map_endpoint(query: str, filename: str):
    """Process a single document - called in parallel by client."""
    print(f"LOG:\t/map - Processing {filename}...")

    try:
        # Fetch single transcript content
        content_map = await get_transcripts_content_async(DB_NAME, COLLECTION_NAME, [filename])

        if not content_map or filename not in content_map:
            return {"error": f"Transcript {filename} not found"}

        content = content_map[filename]

        # Single LLM call - fast, well within timeout
        response = map_document(query, content)
        print(f"LOG:\t/map - Completed {filename}")

        return {"filename": filename, "response": response}

    except Exception as e:
        print(f"LOG:\t/map error for {filename}: {e}")
        return {"error": str(e), "filename": filename}


@rt("/reduce")
async def reduce_endpoint(request):
    """Consolidate multiple map responses into final answer."""
    body = await request.json()
    query = body.get("query", "")
    responses = body.get("responses", [])

    print(f"LOG:\t/reduce - Consolidating {len(responses)} responses...")

    if not responses:
        return Div(cls="uk-card-secondary p-4")("No responses to consolidate.")

    try:
        # Single response - no reduce needed
        if len(responses) == 1:
            final = responses[0]
        else:
            final = reduce_responses(query, responses)

        print("LOG:\t/reduce - Complete")
        return render_response(final)

    except Exception as e:
        print(f"LOG:\t/reduce error: {e}")
        return Div(cls="uk-card-secondary p-4")(
            "Error consolidating responses. Please try again."
        )


@rt("/load-transcripts")
async def load_transcripts_route():
    """
    Async endpoint to load transcripts from MongoDB.
    Called via HTMX after initial page render.
    Fetches metadata only (no content) for fast loading.
    """
    print("LOG:\tLoading transcripts asynchronously...")

    # Fetch metadata only (no TRANSCRIPT content) - this is fast!
    transcripts_metadata = await load_transcripts_metadata_async(DB_NAME, COLLECTION_NAME)

    print(f"LOG:\tLoaded {len(transcripts_metadata)} transcript metadata entries")

    # Build navigation tree directly (no caching - serverless-friendly)
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
