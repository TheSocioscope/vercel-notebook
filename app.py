from fasthtml.common import *
from fasthtml.svg import *
from monsterui.all import *

from lib.auth import *
from lib.sources import *
from lib.rag import *

from starlette.background import BackgroundTask

DB_NAME = "socioscope_db"
COLLECTION_NAME = "socioscope_documents"

# Choose a theme color (blue, green, red, etc)
hdrs = Theme.neutral.headers(apex_charts=True, highlightjs=True, daisy=True)

# Create your app with the theme
app, rt = fast_app(hdrs=hdrs, live=True)
auth = Auth()
sources = Sources()
messages = Messages()

# Load transcripts documents
transcripts = load_transcripts(DB_NAME, COLLECTION_NAME)
print(f'Loaded {len(transcripts)} transcripts.')

# Build transcripts navigation
transcript_nav = build_navigation(transcripts)

# Build docs for rag
rag_docs = build_rag_docs(transcripts)

@rt
def select(transcript:str):
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

def rag_task(message:str):
    print(f'Waiting for response...')
    messages.append(message)
    docs = [rag_docs[source] for source in sources]
    response = rag(docs=docs, message=message)
    messages.append(response)
    print(messages)

@rt
def ask(message:str):
    # response = f"Response to message={message} on sources={sources}" if len(message) > 0 else ''
    task = BackgroundTask(rag_task(message=message))
    return Div(
        P(cls="uk-card-secondary p-4", header=None)(f"{len(messages)} messages")
    ), task

def TranscriptRow(transcript):
    return DivLAligned(LabelCheckboxX(transcript, id=transcript, cls='space-x-1 space-y-3', 
                                      hx_target='#sources', 
                                      hx_post=select.to(transcript=transcript),
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

DiscussionCard = Card( 
    Div(cls="flex-1 space-y-4")(
        Form(hx_target='#response', 
             hx_post=ask,
             hx_swap='innerHTML')(
            Textarea(rows=5, id="message", cls="uk-textarea h-full p-4", placeholder="Write any question to LLM..."),
            DivRAligned(
                Button("Ask", type="submit", cls=(ButtonT.primary)),
                #Button("History", cls=ButtonT.secondary),
            cls="flex gap-x-4 mt-4")              
        ),
        Div(id="response")
    ),
    header = (H3('Discussion'), Subtitle('Research discussion with selected transcripts')),
    body_cls='pt-0'
)    

ModelCard = Card(
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
    header = (H3('Model'), Subtitle('Models parameters')),
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

"""
LeftPanel = NavContainer(
    *map(lambda x: Li(A(x)), ("Sources", "Discussion", "Parameters")),
    uk_switcher="connect: #component-nav; animation: uk-animation-fade",
    cls=(NavT.primary,"space-y-4 mt-4 w-1/5"))
CenterPanel = Ul(id="component-nav", cls="uk-switcher mt-4 w-2/3")(
            Li(cls="uk-active") (TranscriptsCard(),
            *map(Li, [DiscussionCard(), ParamsCard()])))
"""
LeftPanel = Div(cls="w-1/4")(TranscriptsCard)
CenterPanel = Div(cls="w-1/2")(DiscussionCard)            
RightPanel = Div(cls="space-y-4 w-1/4")(SourcesCard, ModelCard)

AppPage =  Container(
    Header,
    Div(cls="flex gap-x-8 m-0")(LeftPanel, CenterPanel, RightPanel),
    cls="uk-container-expand m-0 p-4"
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

@rt
def authenticate(login: Login):
    print(f"Authenticate with id={login.id}")
    auth.login(login.id, login.secret)
    return RedirectResponse(url='/')

serve()