import os
from fastlite import *
from fasthtml.svg import *
from fasthtml.common import *
from monsterui.all import *
from dotenv import load_dotenv
import markdown
import re
from lib.discussion import *
from lib.sources import *
from lib.sources import parse_transcript, get_unique_speakers
from lib.auth import generate_magic_link, verify_token, is_email_allowed, MagicLinkRequest

load_dotenv()

# Session security configuration
SESSION_SECRET = os.getenv("SESSION_SECRET")
if not SESSION_SECRET:
    raise ValueError("SESSION_SECRET env var not set - generate with: python -c \"import secrets; print(secrets.token_hex(32))\"")
IS_PRODUCTION = os.getenv("VERCEL_ENV") == "production"

DB_NAME = "socioscope_db"


def parse_thinking(response: str):
    """Parse <think> blocks from LLM response and return (thinking, answer) tuple."""
    think_pattern = re.compile(r'<think>(.*?)</think>', re.DOTALL)
    thinking_blocks = think_pattern.findall(response)
    answer = think_pattern.sub('', response).strip()
    thinking = '\n\n'.join(thinking_blocks).strip() if thinking_blocks else None
    return thinking, answer


def render_response(response: str):
    """Render LLM response with thinking blocks displayed separately."""
    thinking, answer = parse_thinking(response)
    elements = []

    if thinking:
        elements.append(
            Details(
                Summary("💭 Model Thinking", cls="thinking-summary"),
                Div(
                    NotStr(markdown.markdown(thinking, extensions=['fenced_code', 'tables'])),
                    cls="thinking-content prose"
                ),
                cls="thinking-block"
            )
        )

    elements.append(
        Div(
            NotStr(markdown.markdown(answer, extensions=['fenced_code', 'tables'])),
            cls="prose max-w-none"
        )
    )

    return Div(*elements, cls="uk-card-secondary mt-4 p-4")


COLLECTION_NAME = "socioscope_documents"
MAX_SESSION_AGE = 7 * 24 * 3600  # days x hours x minutes

# Choose a theme color (blue, green, red, etc)
css = Style(
    """
    /* NOTE:
       Avoid overriding UIkit's `uk-switcher` visibility rules globally.
       The right panel uses `uk-tab` + `uk-switcher`, and forcing `display:flex`
       on `.uk-switcher` or its inactive children will show *both* tabs at once.
     */
    /* Markdown styling */
    .prose h1, .prose h2, .prose h3, .prose h4 { margin-top: 1em; margin-bottom: 0.5em; font-weight: 600; }
    .prose h1 { font-size: 1.5em; }
    .prose h2 { font-size: 1.25em; }
    .prose h3 { font-size: 1.1em; }
    .prose p { margin-bottom: 0.75em; line-height: 1.6; }
    .prose ul, .prose ol { margin-left: 1.5em; margin-bottom: 0.75em; padding-left: 0.5em; }
    .prose ul { list-style-type: disc; }
    .prose ul ul { list-style-type: circle; }
    .prose ul ul ul { list-style-type: square; }
    .prose ol { list-style-type: decimal; }
    .prose ol ol { list-style-type: lower-alpha; }
    .prose ol ol ol { list-style-type: lower-roman; }
    .prose li { margin-bottom: 0.25em; line-height: 1.5; }
    .prose li::marker { color: rgba(255,255,255,0.7); }
    .prose code { background: rgba(0,0,0,0.2); padding: 0.15em 0.4em; border-radius: 4px; font-size: 0.9em; }
    .prose pre { background: rgba(0,0,0,0.3); padding: 1em; border-radius: 6px; overflow-x: auto; margin-bottom: 1em; }
    .prose pre code { background: none; padding: 0; }
    .prose blockquote { border-left: 3px solid rgba(255,255,255,0.3); padding-left: 1em; margin-left: 0; font-style: italic; }
    .prose table { border-collapse: collapse; width: 100%; margin-bottom: 1em; }
    .prose th, .prose td { border: 1px solid rgba(255,255,255,0.2); padding: 0.5em; text-align: left; }
    .prose strong { font-weight: 600; }
    /* Thinking block styling */
    .thinking-block { margin-bottom: 1em; border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; background: rgba(0,0,0,0.15); }
    .thinking-summary { cursor: pointer; padding: 0.75em 1em; font-weight: 500; color: rgba(255,255,255,0.7); user-select: none; }
    .thinking-summary:hover { color: rgba(255,255,255,0.9); }
    .thinking-content { padding: 0 1em 1em 1em; font-size: 0.9em; color: rgba(255,255,255,0.65); border-top: 1px solid rgba(255,255,255,0.1); }
    details[open] .thinking-summary { border-bottom: none; }
    /* Skeleton loading animation */
    @keyframes skeleton-pulse {
        0%, 100% { opacity: 0.4; }
        50% { opacity: 0.7; }
    }
    .skeleton-bar {
        background: linear-gradient(90deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.1) 100%);
        background-size: 200% 100%;
        animation: skeleton-pulse 1.5s ease-in-out infinite;
        border-radius: 4px;
        height: 12px;
        margin-bottom: 8px;
    }
    /* Clean transcript row styling - no borders */
    .transcript-checkbox-wrapper {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
    .transcript-checkbox-wrapper label {
        border: none !important;
        background: transparent !important;
    }
    /* Transcript viewer styles */
    .transcript-viewer {
        max-height: 65vh;
        overflow-y: auto;
        border-radius: 8px;
    }
    .transcript-header {
        position: sticky;
        top: 0;
        background: rgba(30, 30, 35, 0.98);
        padding: 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        z-index: 10;
        backdrop-filter: blur(8px);
    }
    .transcript-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        font-size: 0.85rem;
        color: rgba(255,255,255,0.6);
    }
    .transcript-meta-item {
        display: flex;
        gap: 0.5rem;
    }
    .transcript-meta-label {
        color: rgba(255,255,255,0.4);
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 0.05em;
    }
    .transcript-content {
        padding: 0.5rem;
    }
    .transcript-segment {
        display: grid;
        grid-template-columns: 80px 1fr;
        gap: 0.75rem;
        padding: 0.6rem 0.75rem;
        border-radius: 6px;
        margin-bottom: 0.15rem;
        transition: background 0.15s ease;
        /*
          Performance: transcripts can be very long, and each segment is multiple DOM nodes.
          `content-visibility: auto` lets the browser skip rendering off-screen segments,
          which significantly reduces tab-switch jank and improves scroll performance.
        */
        content-visibility: auto;
        contain-intrinsic-size: 60px;
    }
    .transcript-segment:hover {
        background: rgba(255,255,255,0.03);
    }
    .segment-time {
        font-family: 'JetBrains Mono', 'SF Mono', monospace;
        font-size: 0.7rem;
        color: rgba(255,255,255,0.35);
        padding-top: 0.2rem;
        text-align: right;
    }
    .segment-body {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    .segment-speaker {
        font-weight: 600;
        font-size: 0.8rem;
        letter-spacing: 0.02em;
    }
    .segment-text {
        font-size: 0.875rem;
        line-height: 1.55;
        color: rgba(255,255,255,0.85);
    }
    /* Speaker colors */
    .speaker-0 { color: #f59e0b; }
    .speaker-1 { color: #10b981; }
    .speaker-2 { color: #6366f1; }
    .speaker-3 { color: #ec4899; }
    .speaker-4 { color: #14b8a6; }
    .speaker-5 { color: #f97316; }
    .speaker-6 { color: #8b5cf6; }
    .speaker-7 { color: #06b6d4; }
    .transcript-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-top: 0.6rem;
        padding-top: 0.6rem;
        border-top: 1px solid rgba(255,255,255,0.08);
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.75rem;
    }
    .legend-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
    }
    .view-btn {
        cursor: pointer;
        opacity: 0.4;
        transition: opacity 0.15s ease;
        font-size: 0.9rem;
        padding: 0.2rem 0.4rem;
    }
    .view-btn:hover {
        opacity: 1;
    }
    .transcript-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
    }
    /* Right panel tabs */
    .right-panel-tabs {
        border-bottom: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 1rem;
    }
"""
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
db = database(":memory:")
sources = db.create(Source, pk="filename")
discussion = db.create(Message, pk="order")

# NOTE: We no longer load transcripts at module level!
# This is the key change for fast cold starts on Vercel.
# Transcripts are now loaded asynchronously via /load-transcripts endpoint.
print("LOG:\tApp initialized (transcripts will load asynchronously)")


@threaded
def rag_task(docs: list[dict], query: str):
    print(f'LOG: Send "{query}" for RAG on {len(docs)} documents...')
    try:
        response = send_rag(docs=docs, message=query)
    except:
        discussion.insert(
            Message(
                order=len(discussion()) + 1,
                model="qwen/qwen3-32b",
                question=query,
                contents=docs,
                responses=[],
                final_response="Sorry error in the request, please try again.",
            )
        )
    else:
        discussion.insert(
            Message(
                order=len(discussion()) + 1,
                model="qwen/qwen3-32b",
                question=response["question"],
                contents=response["contents"],
                responses=response["responses"],
                final_response=response["final_response"],
            )
        )


@rt
def rag_response(query: str):
    if discussion():
        return (
            PromptForm(query),
            Div(*[render_response(m.final_response) for m in discussion()]),
        )
    else:
        return (
            Textarea(rows=5, disabled=True, cls="uk-textarea p-4")(query),
            Div(
                cls="uk-card-secondary mt-4 p-4",
                hx_target="#discussion",
                hx_post=rag_response.to(query=query),
                # Only poll while the Discussion tab is active; reduces hidden-tab work/jank.
                hx_trigger="every 1s[document.getElementById('discussion-tab')?.closest('li')?.classList.contains('uk-active')]",
                hx_swap="innerHTML",
            )("Please wait for the answer..."),
        )


@rt
async def ask(query: str, selected: str = ""):
    """Handle RAG query - fetches transcript content on-demand."""
    # Get selected transcript filenames from client-side selection
    selected_filenames = [s.strip() for s in selected.split(",") if s.strip()]

    if not selected_filenames:
        return (
            PromptForm(query),
            Div(cls="uk-card-secondary p-4 mt-4")(
                "Please select at least one source in the transcripts panel."
            ),
        )

    # Fetch transcript content on-demand for selected files
    # This is the lazy loading - we only fetch what we need when we need it
    print(f"LOG:\tFetching content for {len(selected_filenames)} selected transcripts...")
    content_map = await get_transcripts_content_async(DB_NAME, COLLECTION_NAME, selected_filenames)

    if not content_map:
        return (
            PromptForm(query),
            Div(cls="uk-card-secondary p-4 mt-4")(
                "Failed to load transcript content. Please try again."
            ),
        )

    # Build docs for RAG (we need page_content and metadata)
    # For metadata, check if we have it cached in sources, otherwise use minimal metadata
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
        return (
            PromptForm(query),
            Div(cls="uk-card-secondary p-4 mt-4")(
                "Selected transcripts not found. Please try again."
            ),
        )

    # Clear discussion
    for message in discussion():
        discussion.delete(message.order)

    # Run rag task
    rag_task(docs, query)
    return rag_response(query)


def PromptForm(query: str = ""):
    return Form(hx_target="#discussion", hx_post=ask, hx_swap="innerHTML")(
        Input(type="hidden", id="selected-transcripts", name="selected"),
        Textarea(
            rows=5,
            id="query",
            required=True,
            cls="uk-textarea p-4",
            placeholder="Write any question to LLM...",
        )(query),
        DivRAligned(Button("Ask", type="submit", cls=(ButtonT.primary)), cls="mt-4"),
    )


def TranscriptRow(transcript):
    return Div(cls="transcript-row")(
        LabelCheckboxX(
            transcript,
            id=transcript,
            value=transcript,
            cls="space-x-1 space-y-3 transcript-checkbox-wrapper flex-1",
            onchange="updateSourcesList()",
        ),
        Span(
            "📖",
            cls="view-btn",
            hx_get=f"/read-transcript?filename={transcript}",
            hx_target="#reading-panel",
            hx_swap="innerHTML",
            onclick="document.getElementById('reading-tab').click();",
            title="Read transcript"
        )
    )


def ProjectRow(project, records):
    return AccordionItem(
        P(f"{project} ({len(records)})"),
        *[TranscriptRow(record) for record in records],
        title_cls="pt-2 pb-2",
    )


def CountryRow(country, projects):
    return AccordionItem(
        P(f"{country.title()} ({len(projects)})"),
        Accordion(
            *[ProjectRow(project, records) for project, records in projects.items()],
            multiple=True,
            animation=True,
            cls="pl-4",
            id=country,
        ),
        title_cls="pt-2 pb-2",
    )


def TranscriptsSkeleton():
    """Loading skeleton shown while transcripts load from MongoDB."""
    return Div(
        id="transcripts-container",
        hx_get="/load-transcripts",
        hx_trigger="load",
        hx_swap="outerHTML",
    )(
        Card(
            Div(cls="space-y-3 p-2")(
                Div(cls="skeleton-bar", style="width: 70%;"),
                Div(cls="skeleton-bar", style="width: 50%;"),
                Div(cls="skeleton-bar", style="width: 85%;"),
                Div(cls="skeleton-bar", style="width: 60%;"),
                Div(cls="skeleton-bar", style="width: 75%;"),
                Div(cls="skeleton-bar", style="width: 45%;"),
                Div(cls="skeleton-bar", style="width: 80%;"),
                Div(cls="skeleton-bar", style="width: 55%;"),
            ),
            header=(H3("Transcripts"), Subtitle("Loading from database...")),
            body_cls="pt-0",
        )
    )


def TranscriptsCard(transcript_nav: dict, count: int):
    """Render the full transcripts card with navigation."""
    return Div(id="transcripts-container")(
        Card(
            Accordion(
                *[
                    CountryRow(country, projects)
                    for country, projects in transcript_nav.items()
                ],
                multiple=True,
                animation=True,
            ),
            header=(H3("Transcripts"), Subtitle(f"Available transcripts ({count})")),
            body_cls="pt-0",
        )
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


def TranscriptSegmentRow(segment: dict, speaker_index: int):
    """Render a single transcript segment with speaker coloring."""
    return Div(cls="transcript-segment")(
        Div(cls="segment-time")(segment["start_time"]),
        Div(cls="segment-body")(
            Div(cls=f"segment-speaker speaker-{speaker_index % 8}")(segment["speaker"]),
            Div(cls="segment-text")(segment["text"])
        )
    )


def TranscriptViewer(metadata: dict, segments: list[dict], speakers: list[str]):
    """Full transcript viewer with metadata header and conversation display."""
    speaker_colors = ['#f59e0b', '#10b981', '#6366f1', '#ec4899', '#14b8a6', '#f97316', '#8b5cf6', '#06b6d4']
    speaker_to_index = {s: i for i, s in enumerate(speakers)}

    legend_items = [
        Div(cls="legend-item")(
            Div(cls="legend-dot", style=f"background: {speaker_colors[i % 8]}"),
            Span(speaker, cls=f"speaker-{i % 8}")
        )
        for i, speaker in enumerate(speakers)
    ]

    return Div(cls="transcript-viewer")(
        Div(cls="transcript-header")(
            H4(metadata.get("NAME", "Transcript"), cls="mb-2"),
            Div(cls="transcript-meta")(
                Div(cls="transcript-meta-item")(
                    Span("Project:", cls="transcript-meta-label"),
                    Span(metadata.get("PROJECT", "-"))
                ),
                Div(cls="transcript-meta-item")(
                    Span("Location:", cls="transcript-meta-label"),
                    Span(f"{metadata.get('GEOGRAPHY', '-')}, {metadata.get('COUNTRY', '-')}")
                ),
                Div(cls="transcript-meta-item")(
                    Span("Date:", cls="transcript-meta-label"),
                    Span(f"{metadata.get('MONTH', '-')} {metadata.get('YEAR', '-')}")
                ),
                Div(cls="transcript-meta-item")(
                    Span("Type:", cls="transcript-meta-label"),
                    Span(metadata.get("TYPE", "-"))
                ),
            ),
            Div(cls="transcript-legend")(*legend_items) if len(speakers) > 1 else None
        ),
        Div(cls="transcript-content")(
            *[TranscriptSegmentRow(seg, speaker_to_index.get(seg["speaker"], 0)) for seg in segments]
        ) if segments else Div(cls="p-4 text-center opacity-50")("No transcript segments found.")
    )


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


async def _get_parsed_transcript(filename: str):
    cached = _cache_get(filename)
    if cached:
        return cached

    contents = await get_transcripts_content_async(DB_NAME, COLLECTION_NAME, [filename])
    if filename not in contents:
        return None

    transcript_text = contents[filename]

    # metadata from sources cache (best-effort)
    try:
        import json
        source = sources[filename]
        metadata = json.loads(source.metadata) if isinstance(source.metadata, str) else source.metadata
    except Exception:
        metadata = {"NAME": filename}

    segments = parse_transcript(transcript_text)
    speakers = get_unique_speakers(segments)

    payload = {"metadata": metadata, "segments": segments, "speakers": speakers}
    _cache_set(filename, payload)
    return payload


def TranscriptLoadingSkeleton(title: str = "Loading transcript..."):
    return Div(cls="space-y-3 p-2")(
        H4(title, cls="mb-3"),
        Div(cls="skeleton-bar", style="width: 70%;"),
        Div(cls="skeleton-bar", style="width: 90%;"),
        Div(cls="skeleton-bar", style="width: 80%;"),
        Div(cls="skeleton-bar", style="width: 60%;"),
        Div(cls="skeleton-bar", style="width: 85%;"),
    )


def TranscriptLoadMoreSentinel(filename: str, offset: int, limit: int):
    return Div(
        id=f"transcript-load-more-{offset}",
        hx_get=f"/read-transcript-chunk?filename={filename}&offset={offset}&limit={limit}",
        hx_trigger="revealed",
        hx_swap="outerHTML",
        cls="p-4",
    )(TranscriptLoadingSkeleton("Loading more..."))


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
    data = await _get_parsed_transcript(filename)
    if not data:
        return Div(cls="p-4 text-center")(P("Transcript not found.", cls="text-red-400"))

    metadata = data["metadata"]
    segments = data["segments"]
    speakers = data["speakers"]

    total = len(segments)
    chunk = segments[offset: offset + limit]
    speaker_to_index = {s: i for i, s in enumerate(speakers)}

    return Div(cls="transcript-viewer")(
        Div(cls="transcript-header")(
            H4(metadata.get("NAME", "Transcript"), cls="mb-2"),
            Div(cls="transcript-meta")(
                Div(cls="transcript-meta-item")(
                    Span("Project:", cls="transcript-meta-label"),
                    Span(metadata.get("PROJECT", "-")),
                ),
                Div(cls="transcript-meta-item")(
                    Span("Location:", cls="transcript-meta-label"),
                    Span(f"{metadata.get('GEOGRAPHY', '-')}, {metadata.get('COUNTRY', '-')}"),
                ),
                Div(cls="transcript-meta-item")(
                    Span("Date:", cls="transcript-meta-label"),
                    Span(f"{metadata.get('MONTH', '-')} {metadata.get('YEAR', '-')}"),
                ),
                Div(cls="transcript-meta-item")(
                    Span("Type:", cls="transcript-meta-label"),
                    Span(metadata.get("TYPE", "-")),
                ),
            ),
            Div(cls="transcript-legend")(
                *[
                    Div(cls="legend-item")(
                        Div(
                            cls="legend-dot",
                            style=f"background: {['#f59e0b', '#10b981', '#6366f1', '#ec4899', '#14b8a6', '#f97316', '#8b5cf6', '#06b6d4'][i % 8]}",
                        ),
                        Span(speaker, cls=f"speaker-{i % 8}"),
                    )
                    for i, speaker in enumerate(speakers)
                ]
            )
            if len(speakers) > 1
            else None,
        ),
        Div(cls="transcript-content")(
            *[TranscriptSegmentRow(seg, speaker_to_index.get(seg["speaker"], 0)) for seg in chunk],
            TranscriptLoadMoreSentinel(filename, offset + limit, limit) if (offset + limit) < total else None,
        ),
    )


@rt("/read-transcript-chunk")
async def read_transcript_chunk(filename: str, offset: int = 200, limit: int = 200):
    data = await _get_parsed_transcript(filename)
    if not data:
        return Div()

    segments = data["segments"]
    speakers = data["speakers"]
    total = len(segments)
    chunk = segments[offset: offset + limit]

    speaker_to_index = {s: i for i, s in enumerate(speakers)}

    return Div(
        *[TranscriptSegmentRow(seg, speaker_to_index.get(seg["speaker"], 0)) for seg in chunk],
        TranscriptLoadMoreSentinel(filename, offset + limit, limit) if (offset + limit) < total else None,
    )


DiscussionCard = Card(
    Div(id="discussion")(PromptForm()),
    header=(
        H3("Discussion"),
        Subtitle("Research discussion with selected transcripts"),
    ),
    body_cls="pt-0 flex-1 space-y-4",
)

ModelCard = Card(
    NavContainer(
        Select(
            Optgroup(
                map(
                    Option,
                    (
                        "text-davinci-003",
                        "text-curie-001",
                        "text-babbage-001",
                        "text-ada-001",
                    ),
                ),
                label="GPT-3",
            ),
            Optgroup(
                map(
                    Option,
                    (
                        "mistral-medium-2505",
                        "magistral-medium-2506",
                        "mistral-small-2506",
                        "magistral-small-2506",
                    ),
                ),
                label="Mistral",
            ),
            label="Model",
            searchable=True,
        ),
        LabelRange(label="Temperature", value="12"),
        LabelRange(label="Maximum Length", value="80"),
        # LabelRange(label='Top P', value='40'),
        cls="space-y-4",
    ),
    header=(H3("Model"), Subtitle("Models parameters")),
    body_cls="pt-0",
)


def LoginPage(message: str = None):
    return Container(
        DivRAligned(cls=(TextT.bold))("SOCIOSCOPE"),
        DivCentered(cls="flex-1 p-16")(
            DivVStacked(
                H3("Authentication"),
                P("Enter your email to receive a magic link."),
                Form(
                    id="login-form",
                    hx_post="/auth",
                    hx_target="#login-message",
                    hx_swap="innerHTML",
                    hx_disabled_elt="#submit-btn",
                )(
                    Fieldset(
                        LabelInput(label="Email", id="email", type="email", required=True),
                    ),
                    Button(
                        "Send Magic Link",
                        id="submit-btn",
                        type="submit",
                        cls=(ButtonT.primary, "w-full"),
                    ),
                    cls="space-y-6",
                ),
                Div(id="login-message", cls="mt-4 text-center")(
                    P(message) if message else None
                ),
            )
        ),
    )


Header = (
    DivRAligned(
        Button(A("Logout", href="/logout"), cls=ButtonT.ghost),
        P(cls=(TextT.bold))("SOCIOSCOPE"),
    ),
)

# Right panel with tabbed Discussion/Reading inside a single Card


def RightPanelCard():
    return Card(
        # Tab navigation
        # Note: disable tab animation to avoid painting both panels during transitions,
        # which becomes noticeably janky when the Reading tab contains a large transcript DOM.
        Ul(cls="uk-tab", **{"data-uk-tab": "connect: #right-content"})(
            Li(cls="uk-active")(A("Discussion", href="#", id="discussion-tab")),
            Li()(A("Reading", href="#", id="reading-tab")),
        ),
        # Tab content
        Ul(id="right-content", cls="uk-switcher uk-margin")(
            # Discussion tab content
            Li(cls="uk-active")(
                Div(id="discussion")(PromptForm()),
            ),
            # Reading tab content
            Li()(
                Div(id="reading-panel", cls="min-h-[350px]")(
                    Div(cls="p-8 text-center")(
                        P("📖", cls="text-4xl mb-4 opacity-30"),
                        P("Select a transcript to read", cls="opacity-50"),
                        P("Click the 📖 icon next to any transcript", cls="text-sm opacity-30 mt-2")
                    )
                )
            ),
        ),
        header=(H3("Workspace"), Subtitle("Discussion & transcript reading")),
        body_cls="pt-0",
    )


MainLayout = Div(cls="flex gap-6 mt-4")(
    Div(cls="w-1/3")(TranscriptsSkeleton()),
    Div(cls="w-2/3")(RightPanelCard()),
)

AppPage = Container(
    Header,
    MainLayout,
    cls="uk-container-expand m-0 p-4",
)


@rt
def index(session):
    """Main app - requires login."""
    if session.get("email"):
        return (Title("Socioscope"), AppPage())
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


@rt
def logout(session):
    """Clear session and redirect to login."""
    session.clear()
    return RedirectResponse(url="/auth")


# For local development
if __name__ == "__main__":
    serve()

# For Vercel deployment - export the ASGI application
application = app
