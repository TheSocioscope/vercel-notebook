from fasthtml.common import *
from fasthtml.svg import *
from monsterui.all import *

from lib.auth import *
from lib.sources import *
from lib.discussion import *

from fastlite import *

DB_NAME = "socioscope_db"
COLLECTION_NAME = "socioscope_documents"

# Choose a theme color (blue, green, red, etc)
css = Style("""
.uk-switcher .w-1\/4, .uk-switcher .w-1\/2 {width:100%;}
@media screen and (min-width: 1260px) {
    .uk-switcher>:not(.uk-active), .uk-switcher {display:flex} 
    .uk-tab-alt {display:none}
    .uk-switcher .w-1\/4 {width:25%}
    .uk-switcher .w-1\/2 {width:50%;}
    .uk-card {width:100%}
} 
"""
)
hdrs = (Theme.neutral.headers(apex_charts=True, highlightjs=True, daisy=True), css)

# Create your app with the theme
app, rt = fast_app(hdrs=hdrs, live=True)
auth = Auth()
# sources = Sources()
db = database(':memory:')
sources = db.create(Source, pk='filename')
discussion = db.create(Message, pk='order')

# Load transcripts documents
transcripts = load_transcripts(DB_NAME, COLLECTION_NAME)
print(f'LOG:\tImport {len(transcripts)} transcripts.')

# Build sources library
for transcript in transcripts:
    sources.insert(Source(filename=transcript['FILE'][:-4], 
                          page_content=transcript['TRANSCRIPT'],
                          metadata={k:str(v) for k,v in transcript.items() if k not in ['TRANSCRIPT', '_id']}))
print(f'LOG:\tCreated {len(sources())} sources library.')

# Build transcripts navigation
transcript_nav = build_navigation(transcripts)

@rt
def select(transcript:str):
    sources.update(filename=transcript, selected=not(sources[transcript].selected))
    # print(f"Sources: {[source.filename for source in sources(where="selected=1")]}")
    return Card(
        Div(*[Li(source.filename) for source in sources(order_by='filename', where="selected=1")]),
        header=(H3('Sources'), Subtitle(f'Selected transcripts ({len(sources(where="selected=1"))})')),
    )

@threaded
def rag_task(docs:list[dict], query:str):
    print(f'LOG: Send "{query}" for RAG on {len(docs)} documents...')
    response = send_rag(docs=docs, message=query)
    discussion.insert(Message(order=len(discussion())+1, model='openai:gpt-4o-mini', 
                              question=response['question'], 
                              contents=response['contents'], 
                              responses=response['responses'], 
                              final_response=response['final_response']))

@rt
def rag_response(query:str):
    if discussion():
        return (PromptForm(query), Div(*map(P(cls="uk-card-secondary mt-4 p-4", header=None), [m.final_response for m in discussion()])))
    else:
        return (Textarea(rows=5, disabled=True, cls="uk-textarea p-4")(query),
                Div(cls="uk-card-secondary mt-4 p-4",
                    hx_target='#discussion',
                    hx_post=rag_response.to(query=query),
                    hx_trigger='every 1s', hx_swap='innerHTML')
                    ("Please wait for the answer..."))

@rt
def ask(query:str):
    #print(f"LOG: Send query={query}")
    if sources(where="selected=1"):
        docs = [dict(page_content=source.page_content, metadata=json.loads(source.metadata)) for source in sources(where="selected=1")]
        
        # Clear discussion
        for message in discussion():
            discussion.delete(message.order)
        
        # Run rag task
        rag_task(docs, query)
        return rag_response(query)
    else:
        return (PromptForm(query), Div(cls="uk-card-secondary p-4 mt-4")("Please select at least one source in the left panel."))

def PromptForm(query:str=''): 
    return Form(hx_target='#discussion', hx_post=ask, hx_swap='innerHTML')(
                Textarea(rows=5, id="query", required=True, cls="uk-textarea p-4", placeholder="Write any question to LLM...")(query),
                DivRAligned(Button("Ask", type="submit", cls=(ButtonT.primary)),
                cls="mt-4")) 

def TranscriptRow(transcript):
    return DivLAligned(LabelCheckboxX(transcript, 
                                      id=transcript, cls='space-x-1 space-y-3', 
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
    header=(H3('Sources'), Subtitle(f'Selected transcripts ({len(sources(where="selected=1"))})')),
    body_cls='pt-0',
    id='sources'
)

DiscussionCard = Card(Div(id='discussion')(PromptForm()),
    header = (H3('Discussion'), Subtitle('Research discussion with selected transcripts')),
    body_cls='pt-0 flex-1 space-y-4')    

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
LeftPanel = Div(TranscriptsCard)
CenterPanel = Div(DiscussionCard)            
RightPanel = Div(SourcesCard, #ModelCard
                                        )
Tabs = (TabContainer(
            Li(A("Transcripts", href='#', cls='uk-active')),
            Li(A("Discussions", href='#')),
            Li(A("Sources", href='#')),
            uk_switcher='connect: #component-nav; animation: uk-animation-fade',
            alt=True),
        Div(id="component-nav", cls="flex uk-switcher gap-x-8 mt-4")(
            Div(cls="w-1/4 ")(TranscriptsCard),
            Div(cls="w-1/2")(DiscussionCard),
            Div(cls="w-1/4")(SourcesCard)))

AppPage =  Container(
    Header,
    Tabs,
    #Div(cls="flex gap-x-8 m-0")(LeftPanel, CenterPanel, RightPanel),
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
    print(f"LOG:\tAuthenticate with id={login.id}")
    auth.login(login.id, login.secret)
    return RedirectResponse(url='/')

serve()