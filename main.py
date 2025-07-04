from fasthtml.common import *
from fasthtml.svg import *
from monsterui.all import *
import calendar
from datetime import datetime

# Choose a theme color (blue, green, red, etc)
hdrs = Theme.neutral.headers(apex_charts=True, highlightjs=True, daisy=True)

# Create your app with the theme
app, rt = fast_app(hdrs=hdrs)

transcripts_list = (
    ('FR', (
        ('FR-004', "Bande de cheffes", ("FR-004_debrief_audio.m4a", "FR-004_interview_audio_1.m4a", "FR-004_interview_audio_2.m4a", "FR-004_interview_audio_3.m4a")),
        )),
    ('DK', (
        ('DK-021', "Nordic Harvest", ("DK_021_audio.mp3", "DK_021_video.mp4")),
        )),
    ('CO', (
        ('CO-006', "Urban farmers", ("CO_006_audio.mp3", "CO_006_video.mp4")),
        ('CO-007', "New project", ("CO_007_audio.mp3", "CO_007_video.mp4"))
        ))
)

transcripts = []
projects = []

@rt
def CheckTranscript(transcript:str):
    global transcripts
    if transcript in transcripts:
        transcripts.remove(transcript)
    else:
        transcripts.append(transcript)
    print(f"Transcripts: {transcripts}")
    result = *[Li(transcript) for transcript in sorted(transcripts)],
    return result

def TranscriptRow(transcript):
    return DivLAligned(LabelCheckboxX(transcript, id=transcript, cls='space-x-1 space-y-3', hx_target='#transcripts', hx_post=CheckTranscript.to(transcript=transcript)))
    #return DivLAligned(CheckboxX(FormLabel(record), cls='space-x-2 space-y-3'))

def ProjectRow(project):
    project_name = project[0] + ' - ' + project[1]
    return AccordionItem(
        project_name,
        *[TranscriptRow(record) for record in project[2]],
    )

def CountryRow(country, projects):
    return AccordionItem(
        P(country), 
        Accordion(
            *[ProjectRow(project) for project in projects],
            multiple=True,
            animation=True,
            cls="pl-4",
            id=country
        )
    )

TranscriptsCard = Card(
    Accordion(
        *[CountryRow(*row) for row in transcripts_list],
        multiple=True,
        animation=True
    ),
    header = (H3('Transcripts'),Subtitle('Available transcripts')),
    body_cls='pt-0'
)

SourcesCard = Card(
    Div(id="transcripts"),
    header = (H3('Sources'), Subtitle('Selected transcripts')),
    body_cls='pt-0',
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
    return Title("NotebookLM"), Container(Grid(
            *map(Div,(
                      Div(TranscriptsCard, cls='space-y-4'),
                      Div(SourcesCard, PromptCard, cls='space-y-4'),
                      Div(ParamsCard, cls='space-y-4'))),
         cols_md=1, cols_lg=3, cols_xl=3))

@rt
def index():
    return Main()

serve()