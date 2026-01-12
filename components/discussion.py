"""Discussion and workspace UI components."""
import re
import markdown
from fasthtml.common import *
from monsterui.all import *


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


def PromptForm(query: str = ""):
    """Form for submitting RAG queries."""
    return Form(hx_target="#discussion", hx_post="/ask", hx_swap="innerHTML")(
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


def RightPanelCard():
    """Right panel with tabbed Discussion/Reading."""
    return Div(cls="right-panel-container")(
        # Tab navigation - full width tabs
        Ul(cls="uk-tab", style="border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 0;",
           **{"data-uk-tab": "connect: #right-content"})(
            Li(cls="uk-active flex-1 text-center")(A("Discussion", href="#", id="discussion-tab")),
            Li(cls="flex-1 text-center")(A("Reading", href="#", id="reading-tab")),
        ),
        # Tab content
        Ul(id="right-content", cls="uk-switcher")(
            # Discussion tab content
            Li(cls="uk-active")(
                Div(id="discussion", cls="pt-4")(PromptForm()),
            ),
            # Reading tab content
            Li()(
                Div(id="reading-panel", cls="min-h-[350px] pt-4")(
                    Div(cls="p-8 text-center")(
                        P("📖", cls="text-4xl mb-4 opacity-30"),
                        P("Select a transcript to read", cls="opacity-50"),
                        P("Click the 📖 icon next to any transcript", cls="text-sm opacity-30 mt-2")
                    )
                )
            ),
        ),
    )


def WaitingResponse(query: str):
    """Waiting state shown while RAG query is processing."""
    return (
        Textarea(rows=5, disabled=True, cls="uk-textarea p-4")(query),
        Div(
            cls="uk-card-secondary mt-4 p-4",
            hx_target="#discussion",
            hx_post=f"/rag-response?query={query}",
            # Only poll while the Discussion tab is active; reduces hidden-tab work/jank.
            hx_trigger="every 1s[document.getElementById('discussion-tab')?.closest('li')?.classList.contains('uk-active')]",
            hx_swap="innerHTML",
        )("Please wait for the answer..."),
    )
