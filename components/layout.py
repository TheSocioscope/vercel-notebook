"""Main layout components."""
from fasthtml.common import *
from monsterui.all import *

from components.transcripts import TranscriptsSkeleton
from components.discussion import RightPanelCard


Header = (
    DivRAligned(
        Button(A("Logout", href="/logout"), cls=ButtonT.ghost),
        P(cls=(TextT.bold))("SOCIOSCOPE"),
    ),
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
