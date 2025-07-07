from fasthtml.common import *
from fasthtml.svg import *
from monsterui.all import *
from helpers import *
from dataclasses import dataclass

DB_NAME = "socioscope_db"
COLLECTION_NAME = "socioscope_documents"

# Choose a theme color (blue, green, red, etc)
hdrs = Theme.neutral.headers(apex_charts=True, highlightjs=True, daisy=True)

# Create your app with the theme
app, rt = fast_app(hdrs=hdrs)
auth = Auth()

# Load transcripts documents
transcripts = load_transcripts(DB_NAME, COLLECTION_NAME)
print(f'Loaded {len(transcripts)} transcripts.')

# Build transcripts navigation
transcript_nav = build_navigation(transcripts)

sources = []

@rt
def CheckTranscript(transcript:str):
    global sources
    if transcript in sources:
        sources.remove(transcript)
    else:
        sources.append(transcript)
    print(f"Sources: {sources}")
    return Card(
        Div(*[Li(source) for source in sorted(sources)]),
        header=(H3('Sources'), Subtitle(f'Selected transcripts ({len(sources)})')),
        #body_cls='pt-0',
        #id='sources'
    )
    
def TranscriptRow(transcript):
    return DivLAligned(LabelCheckboxX(transcript, id=transcript, cls='space-x-1 space-y-3', 
                                      hx_target='#sources', 
                                      hx_post=CheckTranscript.to(transcript=transcript),
                                      hx_swap='innerHTML'))

def ProjectRow(project, records):
    return AccordionItem(
        P(f'{project} ({len(records)})'),
        *[TranscriptRow(record) for record in records],
        title_cls='pt-2 pb-2'
    )

def CountryRow(country, projects):
    return AccordionItem(
        P(f'{country.title()} ({len(projects)})'), 
        Accordion(
            *[ProjectRow(project, records) for project, records in projects.items()],
            multiple=True,
            animation=True,
            cls="pl-4",
            id=country
        ),
        title_cls='pt-2 pb-2'
    )

TranscriptsCard = Card(
    Accordion(
        *[CountryRow(country, projects) for country, projects in transcript_nav.items()],
        multiple=True,
        animation=True,
    ),
    header = (H3('Transcripts'), Subtitle(f'Available transcripts ({len(transcripts)})')),
    body_cls='pt-0'
)

SourcesCard = Card(
    Div(),
    header=(H3('Sources'), Subtitle(f'Selected transcripts ({len(sources)})')),
    body_cls='pt-0',
    id='sources'
)

PromptCard = Card(
    header = (H3('Discussion'), Subtitle('Research discussion with selected transcripts')),
    body_cls='pt-0'
)

ParamsCard = Card(
    NavContainer(
        Select(
            Optgroup(map(Option,("text-davinci-003", "text-curie-001", "text-babbage-001", "text-ada-001")), label='GPT-3'),
            Optgroup(map(Option,("mistral-medium-2505", "magistral-medium-2506", "mistral-small-2506", "magistral-small-2506")), label='Mistral'),
            label="Model",
            searchable=True),
        LabelRange(label='Temperature', value='12'),
        LabelRange(label='Maximum Length', value='80'),
        # LabelRange(label='Top P', value='40'),
        cls='space-y-4'
    ),
    header = (H3('Parameters'), Subtitle('Models parameters')),
    body_cls='pt-0',
)

LoginPage = Container(
    DivRAligned(cls=(TextT.bold))("SOCIOSCOPE"),
    DivCentered(cls='flex-1 p-16')(
        DivVStacked(
            H3("Authentication"),
            Form(method="post", action="/authenticate")(
                Fieldset(
                    LabelInput(label='User', id='id'),
                    LabelInput(label='Password', type="password", id='secret')
                ),
                Button("Login", type="submit", cls=(ButtonT.primary, "w-full")),
                cls='space-y-6')
        )
    )
)

Header = DivRAligned(
            Button(A("Logout", href='/logout'), cls=ButtonT.ghost), 
            P(cls=(TextT.bold))("SOCIOSCOPE"),
        ),

LeftPanel = NavContainer(
    *map(lambda x: Li(A(x)), ("Sources", "Discussion", "Parameters")),
    uk_switcher="connect: #component-nav; animation: uk-animation-fade",
    cls=(NavT.primary,"space-y-4 mt-4 w-1/5"))
CenterPanel = Ul(id="component-nav", cls="uk-switcher mt-4 w-2/3")(
            Li(cls="uk-active") (TranscriptsCard(),
            *map(Li, [PromptCard(), ParamsCard()])))
RightPanel = Div(SourcesCard(), cls="mt-4 w-1/3")

AppPage =  Container(
    Header,
    Div(cls="flex gap-x-12")(LeftPanel, CenterPanel, RightPanel)
)

@rt
def index():
    return (Title("Socioscope"), AppPage()) if auth.authenticate() else RedirectResponse(url='/login')
    
@rt
def login():
    return index() if auth.authenticate() else (Title("Socioscope"), LoginPage())

@rt
def logout():
    auth.logout()
    return login()

@dataclass
class Login: id:str; secret:str

@rt
def authenticate(login: Login):
    print(f"Authenticate with id={login.id}")
    auth.login(login.id, login.secret)
    return RedirectResponse(url='/')


serve()