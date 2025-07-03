from fasthtml.common import *
from fasthtml.components import Uk_input_tag
from fasthtml.svg import *
from monsterui.all import *
import calendar
from datetime import datetime

# Choose a theme color (blue, green, red, etc)
hdrs = Theme.neutral.headers(apex_charts=True, highlightjs=True, daisy=True)

# Create your app with the theme
app, rt = fast_app(hdrs=hdrs)

records_list = (
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

records = []

@rt
def CheckRecord(record:str):
    global records
    if record in records:
        records.remove(record)
    else:
        records.append(record)
    print(f"Records: {records}")
    result = *[Li(record) for record in sorted(records)],
    return result

def RecordRow(record):
    return DivLAligned(LabelCheckboxX(record, id=record, cls='space-x-1 space-y-3', hx_target='#records', hx_post=CheckRecord.to(record=record)))
    #return DivLAligned(CheckboxX(FormLabel(record), cls='space-x-2 space-y-3'))

def ProjectRow(project):
    return AccordionItem(
        P(project[0] + ' - ' + project[1]),
        *[RecordRow(record) for record in project[2]],
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

RecordsCard = Card(
    Accordion(
        *[CountryRow(*row) for row in records_list],
        multiple=True,
        animation=True
    ),
    header = (H3('Records'),Subtitle('List of available records')),
    body_cls='pt-0'
)

SourcesCard = Card(
    Div(id="records"),
    header = (H3('Sources'), Subtitle('Selected records')),
    body_cls='pt-0',
)

PromptCard = Card(
    header = (H3('Prompt'), Subtitle('Chat with selected records')),
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
        LabelRange(label='Top P', value='40'),
        cls='space-y-4'
    ),
    header = (H3('Parameters'), Subtitle('Models parameters')),
    body_cls='pt-0',
)

def Cards():
    return Title("NotebookLM"), Container(Grid(
            *map(Div,(
                      Div(RecordsCard, cls='space-y-4'),
                      Div(SourcesCard, PromptCard, cls='space-y-4'),
                      Div(ParamsCard, cls='space-y-4'))),
         cols_md=1, cols_lg=3, cols_xl=3))

@rt
def index():
    return Cards()

serve()