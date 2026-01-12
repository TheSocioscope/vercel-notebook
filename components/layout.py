"""Main layout components."""
from fasthtml.common import *
from monsterui.all import *

from components.transcripts import TranscriptsSkeleton
from components.discussion import RightPanelCard


MainLayout = Div(cls="flex gap-6 mt-4")(
    Div(cls="w-1/3")(TranscriptsSkeleton()),
    Div(cls="w-2/3")(RightPanelCard()),
)

AppPage = Container(
    MainLayout,
    cls="uk-container-expand m-0 p-4",
)
