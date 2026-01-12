"""Main layout components."""
from fasthtml.common import *
from monsterui.all import *

from components.transcripts import TranscriptsSkeleton
from components.discussion import RightPanelCard


AppPage = Div(cls="flex h-full")(
    Div(cls="w-1/3")(TranscriptsSkeleton()),
    Div(cls="w-2/3")(RightPanelCard()),
)
