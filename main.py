from fasthtml.common import *
from fasthtml.svg import *
from monsterui.all import *
import calendar
from datetime import datetime
from helpers import *
from auth import *

# Choose a theme color (blue, green, red, etc)
hdrs = Theme.neutral.headers(apex_charts=True, highlightjs=True, daisy=True)

# Create your app with the theme
app, rt = fast_app(hdrs=hdrs)
oauth = Auth(app, client)

# Load transcripts
transcripts = load_transcripts('data/transcripts.json')
transcript_nav = make_transcript_nav(transcripts)
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
    header = (H3('Prompt'), Subtitle('Chat with selected transcripts')),
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

def Main():
    return Title("SocioscopeLM"), Container(Grid(
            *map(Div,(
                      Div(TranscriptsCard, cls='space-y-4'),
                      Div(SourcesCard, PromptCard, cls='space-y-4'),
                      Div(ParamsCard, cls='space-y-4'))),
         cols_md=1, cols_lg=3, cols_xl=3))

@rt
def index(auth):
    return Main()

@rt
def login(req):
    return Card(P("Not logged in"), A('Log in', href=oauth.login_link(req)))

serve()