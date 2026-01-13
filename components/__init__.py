"""UI components for Socioscope."""

# Transcript components
from components.transcripts import (
    TranscriptRow,
    ProjectRow,
    CountryRow,
    TranscriptsSkeleton,
    TranscriptsCard,
    TranscriptSegmentRow,
    TranscriptLoadingSkeleton,
    TranscriptLoadMoreSentinel,
    TranscriptViewer,
    SPEAKER_COLORS,
)

# Discussion components
from components.discussion import (
    parse_thinking,
    render_response,
    PromptForm,
    ProgressIndicator,
    RightPanelCard,
)

# Layout components
from components.layout import (
    Header,
    AppPage,
)

# Auth components
from components.auth import (
    LoginPage,
)

__all__ = [
    # Transcripts
    "TranscriptRow",
    "ProjectRow",
    "CountryRow",
    "TranscriptsSkeleton",
    "TranscriptsCard",
    "TranscriptSegmentRow",
    "TranscriptLoadingSkeleton",
    "TranscriptLoadMoreSentinel",
    "TranscriptViewer",
    "SPEAKER_COLORS",
    # Discussion
    "parse_thinking",
    "render_response",
    "PromptForm",
    "ProgressIndicator",
    "RightPanelCard",
    # Layout
    "Header",
    "AppPage",
    # Auth
    "LoginPage",
]
