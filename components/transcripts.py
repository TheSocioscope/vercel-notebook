"""Transcript UI components."""
from fasthtml.common import *
from monsterui.all import *


def TranscriptRow(transcript: str):
    """Single transcript row with checkbox and read button."""
    return Div(cls="flex items-center")(
        LabelCheckboxX(
            transcript,
            id=transcript,
            value=transcript,
            cls="space-x-1 space-y-3 transcript-checkbox-wrapper flex-1",
            onchange="updateSourcesList()",
        ),
        Span(
            "📖",
            cls="cursor-pointer",
            hx_get=f"/read-transcript?filename={transcript}",
            hx_target="#reading-panel",
            hx_swap="innerHTML",
            onclick="document.getElementById('reading-tab').click();",
            title="Read transcript"
        )
    )


def ProjectRow(project: str, records: list):
    """Project accordion item containing transcript rows."""
    return AccordionItem(
        P(f"{project} ({len(records)})"),
        *[TranscriptRow(record) for record in records],
        title_cls="pt-2 pb-2",
    )


def CountryRow(country: str, projects: dict):
    """Country accordion item containing project rows."""
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
        cls="h-full border-r border-[hsl(var(--border))]",
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
            cls="rounded-none shadow-none border-none border-r border-[hsl(var(--border))]",
        )
    )


def TranscriptsCard(transcript_nav: dict, count: int):
    """Render the full transcripts card with navigation."""
    return Div(id="transcripts-container", cls="h-full border-r border-[hsl(var(--border))]")(
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
            body_cls="pt-0 overflow-y-auto flex-1 min-h-0",
            cls="rounded-none shadow-none border-none",
        )
    )


def TranscriptSegmentRow(segment: dict):
    """Render a single transcript segment with speaker coloring."""
    return Div(cls="transcript-segment")(
        Div(cls="segment-time")(segment["start_time"]),
        Div(cls="segment-body")(
            Div(cls="segment-speaker text-xs font-light uppercase text-[hsl(var(--foreground))]")(segment["speaker"]),
            Div(cls="segment-text")(segment["text"])
        )
    )


def TranscriptLoadingSkeleton(title: str = "Loading transcript..."):
    """Generic loading skeleton for transcript content."""
    return Div(cls="space-y-3 p-2")(
        H4(title, cls="mb-3"),
        Div(cls="skeleton-bar", style="width: 70%;"),
        Div(cls="skeleton-bar", style="width: 90%;"),
        Div(cls="skeleton-bar", style="width: 80%;"),
        Div(cls="skeleton-bar", style="width: 60%;"),
        Div(cls="skeleton-bar", style="width: 85%;"),
    )


def TranscriptLoadMoreSentinel(filename: str, offset: int, limit: int):
    """Infinite scroll sentinel that triggers loading more segments."""
    return Div(
        id=f"transcript-load-more-{offset}",
        hx_get=f"/read-transcript-chunk?filename={filename}&offset={offset}&limit={limit}",
        hx_trigger="revealed",
        hx_swap="outerHTML",
        cls="p-4",
    )(TranscriptLoadingSkeleton("Loading more..."))


# Speaker colors for transcript legend
SPEAKER_COLORS = [
    '#f59e0b', '#10b981', '#6366f1', '#ec4899',
    '#14b8a6', '#f97316', '#8b5cf6', '#06b6d4'
]


def TranscriptViewer(metadata: dict, segments: list, speakers: list, offset: int, limit: int, filename: str):
    """Full transcript viewer with header, legend, and content."""
    total = len(segments)
    chunk = segments[offset: offset + limit]
    speaker_to_index = {s: i for i, s in enumerate(speakers)}

    return Div(cls="transcript-viewer")(
        Div(cls="transcript-header")(
            H4(metadata.get("NAME", "Transcript"), cls="mb-2"),
            Span(metadata.get("PROJECT", "-"), cls="text-[hsl(var(--muted-foreground))]"),
        ),
        Div(cls="transcript-content")(
            *[TranscriptSegmentRow(seg) for seg in chunk],
            TranscriptLoadMoreSentinel(filename, offset + limit, limit) if (offset + limit) < total else None,
        ),
    )
