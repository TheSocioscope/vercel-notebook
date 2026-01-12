"""Authentication UI components."""
from fasthtml.common import *
from monsterui.all import *


def LoginPage(message: str = None):
    """Login page with magic link authentication."""
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
