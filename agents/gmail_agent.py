from langchain.agents.agent_toolkits import GmailToolkit
from langchain import OpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools.gmail.utils import build_resource_service, get_gmail_credentials
from langchain.chat_models import ChatOpenAI
from langchain import LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.prompts import PromptTemplate
from langchain.callbacks import get_openai_callback
from elysium_prompts.email_prompts.email_subject_prompts import elysium_email_subject_template_1
from elysium_prompts.email_prompts.email_body_prompts import (
    elysium_email_body_template_investor_outreach,
    elysium_email_body_template_investor_outreach_v2,
    elysium_email_body_template_investor_outreach_draft,
    elysium_email_body_template_investor_outreach_search,
    elysium_email_body_template_investor_outreach_multistep
)
from db.utils import get_token_from_db
import json
import os



ELYSIUM_DESCRIPTION = """
TAGLINE:
We empower developers to build secure, decentralized AI tailored to individual needs. Customize your AI symphony.

THE PROBLEM:
1. AI Agents are isolated from collaboration with each other, existing business services, and average consumers
2. Fragmentation Hinders AI Adoption: Unity, Efficiency, Compatibility, Entry, & Security

3. Lack of Unity: Disjointed, over-technical user experiences.
- Operational Inefficiency: Reduced productivity.
- Limited Cross-Compatibility: Missed synergistic possibilities.
- Barrier to Entry: Discourages widespread adoption.
- Security Concerns: Inconsistent security protocols.

ELYSIUM'S SOLUTION:
1. Seamless User Experience
- Customize agent personalities and settings for a tailored AI experience.
2. Dynamic Ecosystem Integration
- Integrate multiple AI agents for efficient task management.
3. Unified AI Network
- Sync effortlessly with existing business systems for smooth transitions.
4. Secure and Trustworthy Platform
- Elysium uses a blend of decentralized and conventional security protocols for robust data protection

With Elysium OS, we provide a unified, easy-to-navigate portal for accessing your personalized AI Butler or Chief of Staff. 

OUR OFFERINGS:
1. Elysium OS - web and hologram on PC and Mac
AI Personal Butler or Enterprise Chief of Staff (COS)

Elysium OS provides 24/7 access to your personal Butler—or Chief of Staff for our enterprise customers—across various platforms such as text, voice, and web chat. It serves as the unified portal for managing your AI agents, offers seamless interaction, robust customization, and powerful capabilities

2. Automation Station
The Central Hub for Sourcing and Deploying AI Agents

Automation Station streamlines AI Agent recruitment and deployment. Our dynamic marketplace enables task assignment, seamless collaboration, and easy business integration. We manage agent payments, eliminating API key hassles. Experience automation, simplified.


TARGET CUSTOMER is Developers:

1. Shared Problem We Solve
AI Agents have technical setups are not accessible from a single platform, and lack connectivity to other agents and exiting business services



2. Elysium as a Value-Added Catalyst
 Providing single intuitive entry point for consumers to use their technology via Elysium OS (AI Butler / Chief of Staff)
 Platforming all their AI Agents in one place where transactions between agents or between agents and existing businesses will occur via AutomationStation (Agent recruiting and deployment marketplace)


CAPITAL RAISE:
We are raising
$3,500,000 in our Seed round
The purpose of the fundraising:
1. Significant hirings: UX/UI Designers, OS Lead, Backend & Support Devs
2. Growth via new marketing channels, ready resource for enterprise fufillment, and scaling audits
3. Development: Full build of our platform/ public launch
"""

pitch_content = """
TAGLINE:::
We empower developers to build secure, decentralized AI tailored to individual needs. Customize your AI symphony.

THE PROBLEM:::
1. AI Agents are isolated from collaboration with each other, existing business services, and average consumers
2. Fragmentation Hinders AI Adoption: Unity, Efficiency, Compatibility, Entry, & Security
3. Lack of Unity: Disjointed, over-technical user experiences.
- Operational Inefficiency: Reduced productivity.
- Limited Cross-Compatibility: Missed synergistic possibilities.
- Barrier to Entry: Discourages widespread adoption.
- Security Concerns: Inconsistent security protocols.

ELYSIUM'S SOLUTION:::
1. Seamless User Experience
- Customize agent personalities and settings for a tailored AI experience.
2. Dynamic Ecosystem Integration
- Integrate multiple AI agents for efficient task management.
3. Unified AI Network
- Sync effortlessly with existing business systems for smooth transitions.
4. Secure and Trustworthy Platform
- Elysium uses a blend of decentralized and conventional security protocols for robust data protection
With Elysium OS, we provide a unified, easy-to-navigate portal for accessing your personalized AI Butler or Chief of Staff. 

OUR OFFERINGS:::
1. Elysium OS - web and hologram on PC and Mac
AI Personal Butler or Enterprise Chief of Staff (COS)

Elysium OS provides 24/7 access to your personal Butler—or Chief of Staff for our enterprise customers—across various platforms such as text, voice, and web chat. It serves as the unified portal for managing your AI agents, offers seamless interaction, robust customization, and powerful capabilities

2. Automation Station
The Central Hub for Sourcing and Deploying AI Agents

Automation Station streamlines AI Agent recruitment and deployment. Our dynamic marketplace enables task assignment, seamless collaboration, and easy business integration. We manage agent payments, eliminating API key hassles. Experience automation, simplified.

TARGET CUSTOMER:::
Developers:

1. Shared Problem We Solve
AI Agents have technical setups are not accessible from a single platform, and lack connectivity to other agents and exiting business services

2. Elysium as a Value-Added Catalyst
Providing single intuitive entry point for consumers to use their technology via Elysium OS (AI Butler / Chief of Staff)
Platforming all their AI Agents in one place where transactions between agents or between agents and existing businesses will occur via AutomationStation (Agent recruiting and deployment marketplace)

CAPITAL RAISE:::
We are raising
$3,500,000 in our Seed round
The purpose of the fundraising:
1. Significant hirings: UX/UI Designers, OS Lead, Backend & Support Devs
2. Growth via new marketing channels, ready resource for enterprise fulfillment, and scaling audits
3. Development: Full build of our platform/ public launch

Our Team:::
Our experienced team of AI experts and industry veterans is dedicated to achieving our mission.

Michael Gruen
Chief Executive Officer

Doug Schaer
Chief Business Officer

Peter Krenesky
CTO

Arben Gutierrez-B.
Head of Product

Michael Daigler
VP of Engineering

Oversight Committee:::
Yohei Nakajima
AI Solutions Architectural Consultant, Scholar-in-Residence

Brock Pierce
Chief Evangelist

Elysium's Advisors:::
World-Class Advisors whose expertise and experience are sure to guide Elysium to Success

Marc Randolph
Co-founder and first CEO of Netflix (NFLX:NASDAQ), Marc is a seasoned Silicon Valley entrepreneur and investor. His portfolio includes Looker Data Sciences, Chubbies Shorts, and MentorBox, etc.

G. Scott Paterson
Director of Lionsgate Entertainment Canada Corp (LGF.A:NYSE), Scott is an accomplished investment banker with 30+ years of experience in tech and media sectors. He has served as CEO / Board of Yorkton Securities, NeuLion, QYOU (TSX.V: QYOU), and more.

Anthony Scaramucci
Former White House Director of Communications and founder of SkyBridge Capital, Anthony is a well-known financier and political commentator. His extensive career highlights include stints at Goldman Sachs and Lehman Brothers.

Jay Abraham
Mentor of Mentors, Jay is the founder and CEO of The Abraham Group, and has advised over 10,000 clients across 400+ industries, generating billions in revenue. Innovator behind "Three Ways to Grow a Business" model, Jay is a sought-after author, speaker, and mentor in the field of business growth and marketing.

Ory Rinat
Former Chief Digital Officer at The White House and Founder & CEO of Urban Legend. Ory has been at the forefront of digital strategies and political campaigns. A Columbia and Georgetown Law alumnus, Ory's innovation now drives his influencer marketing tech venture in D.C.

Dr. Jeffrey Pfeffer
Professor at Stanford’s Graduate School of Business, Jeffrey is a revered figure in organizational behavior. As a thought leader in business theories he has written 16 influential books, is involved in Business 2.0 and Fortune.com, and has served on the boards of Quantum Leap Healthcare, SonoSite, etc.
"""


def _generate_token_file():
    token = get_token_from_db(user_id='dev_123')
    with open('token.json', 'w') as file:
            json.dump(token, file)

def _clean_up_token_file():
    if os.path.exists('token.json'):
        os.remove('token.json')
    else:
        print("The file does not exist")
def _build_gmail_agent():
    toolkit = GmailToolkit()

    # Can review scopes here https://developers.google.com/gmail/api/auth/scopes
    # For instance, readonly scope is 'https://www.googleapis.com/auth/gmail.readonly'
    credentials = get_gmail_credentials(
        token_file="token.json",
        scopes=["https://mail.google.com/"],
        client_secrets_file="credentials.json",
        # client_secrets_file="desktop-creds2.json",

    )
    api_resource = build_resource_service(credentials=credentials)
    toolkit = GmailToolkit(api_resource=api_resource)

    tools = toolkit.get_tools()
    llm = OpenAI(temperature=0)
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        
    )
    return agent


def generate_email_subject(email_body: str, prompt_template):
    human_message_prompt = HumanMessagePromptTemplate.from_template(
            template=prompt_template
        )
    chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])
    with get_openai_callback() as cb:
        chat = ChatOpenAI(temperature=0.08)
        result = chat(
            chat_prompt.format_prompt(
                email_body=email_body,
            ).to_messages()
        )

        content = result.content

        # Hack to get around OpenAI's API returning quotes in the content
        cleansed = content.replace("\"", "")

        return cleansed, cb.total_tokens
    
def generate_email_body(
        sender_name: str,
        recipient_name: str,
        entity_name: str,
        selected_body_prompt: str
    ):
    human_message_prompt = HumanMessagePromptTemplate.from_template(
            template=selected_body_prompt
        )
    chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])

    overall_token_usage_from_body_generation = 0

    

    
    prompt = chat_prompt.format_prompt(
            sender_name=sender_name,
            recipient_name=recipient_name,
            entity_name=entity_name
        ).to_messages()

    with get_openai_callback() as cb:
        chat = ChatOpenAI(temperature=0)
        result = chat(prompt)
        overall_token_usage_from_body_generation += cb.total_tokens
    
    return result.content, overall_token_usage_from_body_generation


def run_email_agent(
        name: str,
        email: str,
        entity: str,
        sent_from: str = "Michael",
        entity_website: str = None
    ):
    from deck.deck_generation import create_ppt_text, create_ppt_v4, create_ppt_v5
    from deck.utils import gather_contact_info
    import uuid
    contact_info = gather_contact_info(
        email=email,
        name=name,
        website=entity_website if entity_website else None
    )

    twitter_pfp_img_url = contact_info.get("twitter_image")
    slide_content = create_ppt_text(
        topic=ELYSIUM_DESCRIPTION,
        recipient_name=name,
        entity_name=entity

    )
    tmp_filepath = "slidecontent.txt"
    with open(tmp_filepath, 'w') as file:
        file.write(slide_content)
    
    print('Slide show content', slide_content)
    import random
    random_number = random.randint(1, 7)
    valid_designs = [3]

    slide_res = create_ppt_v5(
        text_file=tmp_filepath,
        design_number=2,
        ppt_name=f'{name}-{entity}-{str(uuid.uuid4())}',
        twitter_pfp_img_url=twitter_pfp_img_url
    )
    _generate_token_file()

    agent = _build_gmail_agent()
    prompt_template_step_1 = PromptTemplate.from_template(template=elysium_email_body_template_investor_outreach_multistep)

    formatted_prompt_step_1 = prompt_template_step_1.format(recipient_name=name, email=email, entity_name=entity, sent_from=sent_from)

    result = agent.run(formatted_prompt_step_1)
    _clean_up_token_file()
    # prompt_template = PromptTemplate.from_template(template=elysium_email_body_template_investor_outreach)
    # prompt_template = PromptTemplate.from_template(template=elysium_email_body_template_investor_outreach_v2)
   
    
    # prompt_template_step_2 = PromptTemplate.from_template(template=elysium_email_body_template_investor_outreach_search)
    # formatted_prompt_step_2 = prompt_template_step_2.format(email=email)
    # result_2 = agent.run(formatted_prompt_step_2)
    # print(result_2)


