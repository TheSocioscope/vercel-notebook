from fasthtml.common import *
from fasthtml.components import Uk_input_tag
from fasthtml.svg import *
from monsterui.all import *
import calendar
from datetime import datetime

# Choose a theme color (blue, green, red, etc)
hdrs = Theme.blue.headers(apex_charts=True, highlightjs=True, daisy=True)

# Create your app with the theme
app, rt = fast_app(hdrs=hdrs)

CreateAccount = Card(
    Grid(Button(DivLAligned(UkIcon('github'),Div('Github'))),Button('Google')),
            DividerSplit("OR CONTINUE WITH", text_cls=TextPresets.muted_sm),
            LabelInput('Email',    id='email',   placeholder='m@example.com'),
            LabelInput('Password', id='password',placeholder='Password', type='Password'),
            header=(H3('Create an Account'),Subtitle('Enter your email below to create your account')),
            footer=Button('Create Account',cls=(ButtonT.primary,'w-full')))

PaypalSVG_data = "M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944.901C5.026.382 5.474 0 5.998 0h7.46c2.57 0 4.578.543 5.69 1.81 1.01 1.15 1.304 2.42 1.012 4.287-.023.143-.047.288-.077.437-.983 5.05-4.349 6.797-8.647 6.797h-2.19c-.524 0-.968.382-1.05.9l-1.12 7.106zm14.146-14.42a3.35 3.35 0 0 0-.607-.541c-.013.076-.026.175-.041.254-.93 4.778-4.005 7.201-9.138 7.201h-2.19a.563.563 0 0 0-.556.479l-1.187 7.527h-.506l-.24 1.516a.56.56 0 0 0 .554.647h3.882c.46 0 .85-.334.922-.788.06-.26.76-4.852.816-5.09a.932.932 0 0 1 .923-.788h.58c3.76 0 6.705-1.528 7.565-5.946.36-1.847.174-3.388-.777-4.471z"
AppleSVG_data = "M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"
Card1Svg  = Svg(viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_linecap="round", stroke_linejoin="round", stroke_width="2", cls="h-6 w-6 mr-1")(Rect(width="20", height="14", x="2", y="5", rx="2"),Path(d="M2 10h20"))
PaypalSvg = Svg(role="img", viewBox="0 0 24 24", cls="h-6 w-6 mr-1")(Path(d=PaypalSVG_data, fill="currentColor")),
AppleSvg  = Svg(role="img", viewBox="0 0 24 24", cls="h-6 w-6 mr-1")(Path(d=AppleSVG_data, fill="currentColor"))

PaymentMethod = Card(
    Grid(Button(DivCentered(Card1Svg,  "Card"),   cls='h-20 border-2 border-primary'),
         Button(DivCentered(PaypalSvg, "PayPal"), cls='h-20'),
         Button(DivCentered(AppleSvg,  "Apple"),  cls='h-20')),
    Form(LabelInput('Name',        id='name',        placeholder='John Doe'),
         LabelInput('Card Number', id='card_number', placeholder='m@example.com'),
         Grid(LabelSelect(*Options(*calendar.month_name[1:],selected_idx=0),label='Expires',id='expire_month'),
              LabelSelect(*Options(*range(2024,2030),selected_idx=0),       label='Year',   id='expire_year'),
              LabelInput('CVV', id='cvv',placeholder='CVV', cls='mt-0'))),
        header=(H3('Payment Method'),Subtitle('Add a new payment method to your account.')))

area_opts = ('Team','Billing','Account','Deployment','Support')
severity_opts = ('Severity 1 (Highest)', 'Severity 2', 'Severity 3', 'Severity 4 (Lowest)')
ReportIssue = Card(
    Grid(Div(LabelSelect(*Options(*area_opts),    label='Area',    id='area')),
         Div(LabelSelect(*Options(*severity_opts),label='Severity',id='area'))),
    LabelInput(    label='Subject',     id='subject',    placeholder='I need help with'),
    LabelTextArea( label='Description', id='description',placeholder='Please include all information relevant to your issue'),
    Div(FormLabel('Tags', fr='#tags'),
        Uk_input_tag(name="Tags",state="danger", value="Spam,Invalid", uk_cloak=True, id='tags')),
    header=(H3('Report Issue'),Subtitle('What area are you having problems with?')),
    footer = DivFullySpaced(Button('Cancel'), Button(cls=ButtonT.primary)('Submit')))

monster_desc ="Python-first beautifully designed components because you deserve to focus on features that matter and your app deserves to be beautiful from day one."
MonsterUI = Card(H4("Monster UI"),
              Subtitle(monster_desc),
              DivLAligned(
                    Div("Python"),
                    DivLAligned(UkIcon('star'),Div("20k"), cls='space-x-1'),
                    Div(datetime.now().strftime("%B %d, %Y")),
                    cls=('space-x-4',TextPresets.muted_sm)))

def CookieTableRow(heading, description, active=False):
    return Tr(Td(H5(heading)),
              Td(P(description, cls=TextPresets.muted_sm)),
              Td(Switch(checked=active)))

CookieSettings = Card(
    Table(Tbody(
        CookieTableRow('Strictly Necessary', 'These cookies are essential in order to use the website and use its features.', True),
        CookieTableRow('Functional Cookies', 'These cookies allow the website to provide personalized functionality.'),
        CookieTableRow('Performance Cookies', 'These cookies help to improve the performance of the website.'))),
    header=(H4('Cookie Settings'),Subtitle('Manage your cookie settings here.')),
    footer=Button('Save Preferences', cls=(ButtonT.primary, 'w-full')))

team_members = [("Sofia Davis", "m@example.com", "Owner"),("Jackson Lee", "p@example.com", "Member"),]
def TeamMemberRow(name, email, role):
    return DivFullySpaced(
        DivLAligned(
            DiceBearAvatar(name, 10,10),
            Div(P(name, cls=(TextT.sm, TextT.medium)),
                P(email, cls=TextPresets.muted_sm))),
        Button(role, UkIcon('chevron-down', cls='ml-4')),
        DropDownNavContainer(map(NavCloseLi, [
            A(Div('Viewer',    NavSubtitle('Can view and comment.'))),
            A(Div('Developer', NavSubtitle('Can view, comment and edit.'))),
            A(Div('Billing',   NavSubtitle('Can view, comment and manage billing.'))),
            A(Div('Owner',     NavSubtitle('Admin-level access to all resources.')))])))

TeamMembers = Card(*[TeamMemberRow(*member) for member in team_members],
        header = (H4('Team Members'),Subtitle('Invite your team members to collaborate.')))

access_roles = ("Read and write access", "Read-only access")
team_members = [("Olivia Martin", "m@example.com", "Read and write access"),
                ("Isabella Nguyen", "b@example.com", "Read-only access"),
                ("Sofia Davis", "p@example.com", "Read-only access")]

def TeamMemberRow(name, email, role):
    return DivFullySpaced(
        DivLAligned(DiceBearAvatar(name, 10,10),
                    Div(P(name, cls=(TextT.sm, TextT.medium)),
                        P(email, cls=TextPresets.muted_sm))),
        Select(*Options(*access_roles, selected_idx=access_roles.index(role))))

ShareDocument = Card(
    DivLAligned(Input(value='http://example.com/link/to/document'),Button('Copy link', cls='whitespace-nowrap')),
    Divider(),
    H4('People with access', cls=TextPresets.bold_sm),
    *[TeamMemberRow(*member) for member in team_members],
    header = (H4('Share this document'),Subtitle('Anyone with the link can view this document.')))

DateCard = Card(Button('Jan 20, 2024 - Feb 09, 2024'))

section_content =(('bell','Everything',"Email digest, mentions & all activity."), 
                  ('user',"Available","Only mentions and comments"),
                  ('ban', "Ignoring","Turn of all notifications"))

def NotificationRow(icon, name, desc):
    return Li(cls='-mx-1')(A(DivLAligned(UkIcon(icon),Div(P(name),P(desc, cls=TextPresets.muted_sm)))))

Notifications = Card(
    NavContainer(
        *[NotificationRow(*row) for row in section_content],
        cls=NavT.secondary),
    header = (H4('Notification'),Subtitle('Choose what you want to be notified about.')),
    body_cls='pt-0')

TeamCard = Card(
    DivLAligned(
        DiceBearAvatar("Isaac Flath", h=24, w=24),
        Div(H3("Isaac Flath"), P("Library Creator"))),
    footer=DivFullySpaced(
        DivHStacked(UkIcon("map-pin", height=16), P("Alexandria, VA")),
        DivHStacked(*(UkIconLink(icon, height=16) for icon in ("mail", "linkedin", "github")))),
    cls=CardT.hover)


project_list =(('bell','FR-004',"Bande de cheffes"), 
                ('user',"DK-021","Nordic Harvest"),
                ('ban', "CO-006","Urban farmers"))

def ProjectRow(icon, name, desc):
    return Li(cls='-mx-1')(A(DivLAligned(UkIcon(icon),Div(P(name),P(desc, cls=TextPresets.muted_sm)))))

ProjectsCard = Card(
    NavContainer(
        *[ProjectRow(*row) for row in project_list],
        cls=NavT.secondary),
    header = (H3('Projects'),Subtitle('List of available projects')),
    body_cls='pt-0'
)

def RecordsRow(name):
    return Li(cls='-mx-1')(A(DivLAligned(UkIcon(icon='check') ,Div(P(name)))))

records_list = (("FR-004_debrief_audio.m4a"),
                ("FR-004_interview_audio_1.m4a"),
                ("FR-004_interview_audio_2.m4a"),
                ("FR-004_interview_audio_3.m4a"))

RecordsCard = Card(
    NavContainer(
        *[RecordsRow(row) for row in records_list],
        cls=NavT.secondary),
    header = (H3('Records'),Subtitle('List of available records')),
    body_cls='pt-0'
)

def Cards():
    return Title("Cards Example"), Container(Grid(
            *map(Div,(
                      Div(ProjectsCard, RecordsCard, CreateAccount, TeamCard, cls='space-y-4'),
                      Div(TeamMembers, ShareDocument,DateCard,Notifications, cls='space-y-4'),
                      Div(ReportIssue,MonsterUI,CookieSettings, cls='space-y-4'))),
         cols_md=1, cols_lg=2, cols_xl=3))

@rt
def index():
    return Cards()

serve()