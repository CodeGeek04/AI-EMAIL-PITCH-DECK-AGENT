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
from agents.scheduler import get_user_service
from agents.toolkits.custom_gmail_toolkit import CustomGmailToolkit

from elysium_prompts.deck_prompts.pitch_deck_prompts import pitch_content
from elysium_prompts.email_prompts.email_subject_prompts import elysium_email_subject_template_1
from elysium_prompts.email_prompts.email_body_prompts_manual import elysium_email_body_template_investor_outreach_v2, elysium_email_body_template_investor_outreach_v3

from db.utils import get_token_from_db, save_message_metadata_to_firestore, save_thread_to_firestore, add_message_to_thread
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


def _generate_token_file():
    token = get_token_from_db(user_id='dev_123')
    with open('token.json', 'w') as file:
            json.dump(token, file)

def _generate_firestore_token_file():
    from db.utils import get_token_from_firestore
    token = get_token_from_firestore(user_id='dev_123')
    with open('token.json', 'w') as file:
            json.dump(token, file)

def _clean_up_token_file():
    if os.path.exists('token.json'):
        os.remove('token.json')
    else:
        print("The file does not exist")




def _get_gmail_credentials():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    # Load credentials from token.json
    credentials = Credentials.from_authorized_user_file("token.json", scopes=["https://mail.google.com/"])

    # If credentials are expired but have a refresh token, then refresh them
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        # Optionally save the refreshed credentials back to token.json
        with open("token.json", "w") as token:
            token.write(credentials.to_json())

    api_resource = build_resource_service(credentials=credentials)

    return credentials, api_resource

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
        recipient_email: str,
        entity_name: str,
        selected_body_prompt: str,
        sent_from: str
        
    ):
    human_message_prompt = HumanMessagePromptTemplate.from_template(
            template=selected_body_prompt
        )
    chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])

    overall_token_usage_from_body_generation = 0
    print("sender name", sender_name)
    print("Recipient email:", recipient_email)
    print("Entity:", entity_name)
    print("sent from: ", sent_from)
    print("recipient name:", recipient_name)
    

    elysium_demo_site =  "https://AutomationStation.org"
    elysium_deck_link = "https://view.storydoc.com/z3D4YevW"
    prompt = chat_prompt.format_prompt(
            sent_from=sender_name,
            recipient_name=recipient_name,
            entity_name=entity_name,
            email=recipient_email,
            link_to_deck=elysium_deck_link,
            demo_link=elysium_demo_site
        ).to_messages()

    with get_openai_callback() as cb:
        chat = ChatOpenAI(temperature=0)
        result = chat(prompt)
        overall_token_usage_from_body_generation += cb.total_tokens
    
    return result.content, overall_token_usage_from_body_generation



from googleapiclient.discovery import build
from email.message import EmailMessage
import base64
import mimetypes
import textwrap

def send_draft_email_with_attachment(
        email_body, 
        email_subject, 
        sent_from, 
        to_email,
        creds,
        service,
        slide_res_filepath, 
):
    try:
        # Initialize Gmail API client
        # service = build('gmail', 'v1', credentials=creds)

        # Create MIME email
        mime_message = EmailMessage()
        mime_message['To'] = to_email
        mime_message['From'] = sent_from
        mime_message['Subject'] = email_subject
        mime_message.set_content(email_body)

        # Attach the slide to the email
        content_type, _ = mimetypes.guess_type(slide_res_filepath)
        main_type, sub_type = content_type.split('/', 1)
        
        with open(slide_res_filepath, 'rb') as fp:
            attachment_data = fp.read()
        
        mime_message.add_attachment(attachment_data, maintype=main_type, subtype=sub_type, filename=slide_res_filepath.split('/')[-1])

        # Encode the MIME message
        encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

        # Create the draft
        draft = service.users().drafts().create(userId='me', body={'message': {'raw': encoded_message}}).execute()

        # Send the draft
        response = service.users().drafts().send(userId='me', body={'id': draft['id']}).execute()
        print('response', response)
        return response['id'], response['threadId']
    except Exception as e:
        print('Error sending draft', e)



def send_draft_email_with_attachment_text_wrapped(
        email_body, 
        email_subject, 
        sent_from, 
        to_email,
        creds,
        service,
        slide_res_filepath, 
):
    from constants.hermes_scheduler import HERMES_EMAIL
    try:
        # Wrap the email body to a consistent line length (e.g., 72 characters)
        wrapped_email_body = textwrap.fill(email_body, width=148)

        # Initialize Gmail API client
        # service = build('gmail', 'v1', credentials=creds)

        # Create MIME email
        mime_message = EmailMessage()
        mime_message['To'] = to_email
        mime_message['From'] = sent_from
        mime_message['Subject'] = email_subject
        mime_message['Cc'] = HERMES_EMAIL
        mime_message.set_content(wrapped_email_body)

        # Attach the slide to the email
        content_type, _ = mimetypes.guess_type(slide_res_filepath)
        main_type, sub_type = content_type.split('/', 1)
        
        with open(slide_res_filepath, 'rb') as fp:
            attachment_data = fp.read()
        
        mime_message.add_attachment(attachment_data, maintype=main_type, subtype=sub_type, filename=slide_res_filepath.split('/')[-1])

        # Encode the MIME message
        encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

        # Create the draft
        draft = service.users().drafts().create(userId='me', body={'message': {'raw': encoded_message}}).execute()

        # Send the draft
        response = service.users().drafts().send(userId='me', body={'id': draft['id']}).execute()
        print('response', response)
        return response['id'], response['threadId']
    except Exception as e:
        print('Error sending draft', e)



def send_draft_email_with_attachment_text_wrapped_v2(
        email_body, 
        email_subject, 
        sent_from, 
        to_email,
        creds,
        service,
        slide_res_filepath, 
):
    from constants.hermes_scheduler import HERMES_EMAIL
    try:
        # Wrap the email body to a consistent line length (e.g., 72 characters)
        # wrapped_email_body = textwrap.fill(email_body, width=72)
        print(email_body)
        # Create MIME email
        mime_message = EmailMessage()
        mime_message['To'] = to_email
        mime_message['From'] = sent_from
        mime_message['Subject'] = email_subject
        mime_message['Cc'] = HERMES_EMAIL
        mime_message.set_content(email_body)
        # mime_message.set_content(wrapped_email_body)  # for plain text
        mime_message.add_alternative('<p>' + email_body.replace('\n', '<br>') + '</p>', subtype='html')  # for HTML


        # Attach the slide to the email
        content_type, _ = mimetypes.guess_type(slide_res_filepath)
        main_type, sub_type = content_type.split('/', 1)
        
        with open(slide_res_filepath, 'rb') as fp:
            attachment_data = fp.read()
        
        mime_message.add_attachment(attachment_data, maintype=main_type, subtype=sub_type, filename=slide_res_filepath.split('/')[-1])

        # Encode the MIME message
        encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

        # Create the draft
        draft = service.users().drafts().create(userId='me', body={'message': {'raw': encoded_message}}).execute()

        # Send the draft
        response = service.users().drafts().send(userId='me', body={'id': draft['id']}).execute()

        # Fetch the full email details to obtain the Message-ID header
        full_message = service.users().messages().get(userId='me', id=response['id']).execute()
        print(full_message)
        message_headers = full_message.get('payload', {}).get('headers', [])
        print('headers', message_headers)
        message_id_header = None

        for header in message_headers:
            if header["name"] == "Message-Id":
                message_id_header = header['value']
                break

        print('response', response)
        print('Message-Id', message_id_header)

        print("Preparing to return values...")
        return_values = (response['id'], response['threadId'], message_id_header)
        print("Return values:", return_values)
        return return_values
    except Exception as e:
        print('Error sending draft', e)
        return None, None, None  


def run_email_agent_v2(
    name: str,
    email: str,
    entity: str,
    sent_from: str = "Michael",
    entity_website: str = None  
):
    from deck.deck_generation import create_ppt_text, create_ppt_v4, create_ppt_v5
    from deck.utils import gather_contact_info
    from db.utils import EmailStatus, AgentOwnerStatus
    import datetime
    import uuid

    print('getting credentials')
    _generate_firestore_token_file() 

    gmail_credentials, api_resource = _get_gmail_credentials()


    print(entity_website)
    contact_info = gather_contact_info(
        email=email,
        name=name,
        website=entity_website if entity_website else None
    )
    print("contact info", contact_info)
    entity_info = contact_info.get("entity_info")
    twitter_pfp_img_url = contact_info.get("twitter_image")
    # recent_tweets = contact_info.get("recent_tweets")
    
  

    slide_content = create_ppt_text(
        topic=ELYSIUM_DESCRIPTION,
        recipient_name=name,
        entity_name=entity,
        entity_info=entity_info,
    )

    tmp_filepath = "slidecontent.txt"
    with open(tmp_filepath, 'w') as file:
        file.write(slide_content)

    # print('Slide show content', slide_content)
    import random
    random_number = random.randint(1, 7)
    valid_designs = [6]

    slide_res_filepath = create_ppt_v5(
        text_file=tmp_filepath,
        design_number=6,
        ppt_name=f'{name}-{entity}-{str(uuid.uuid4())}',
        twitter_pfp_img_url=twitter_pfp_img_url
    )
    print("generating email body:\n")
    print("sender name", sent_from)
    print("Recipient email:", email)
    print("Entity:", entity)
    print("sent from: ", sent_from)
    print("recipient name:", name)
    service = get_user_service(user_id='dev_123')
    
    profile = service.users().getProfile(userId='me').execute()
    email_address = profile['emailAddress']
    email_body, tokens_used_for_body = generate_email_body(
        sender_name=sent_from,
        recipient_name=name,
        recipient_email=email,
        entity_name=entity,
        selected_body_prompt=elysium_email_body_template_investor_outreach_v3,
        sent_from=email_address
    )

    email_subject, tokens_used_for_subject = generate_email_subject(
        email_body=email_body,
        prompt_template=elysium_email_subject_template_1
    )
    
    message_id, thread_id, message_id_header = send_draft_email_with_attachment_text_wrapped_v2(
        email_body=email_body,
        email_subject=email_subject,
        sent_from=sent_from,
        to_email=email,
        creds=gmail_credentials,
        service=api_resource,
        slide_res_filepath=slide_res_filepath
    )
    timestamp_sent = datetime.datetime.now().isoformat()

    print("Email sent with messageId: ", message_id)
    save_message_metadata_to_firestore(
        message_id=message_id,
        metadata={
            'email_body': email_body,
            'email_subject': email_subject,
            'sent_from': sent_from,
            'owner': AgentOwnerStatus.EMAILER.value,
            'to_email': email,
            'slide_filepath': slide_res_filepath,
            'timestamp_sent': timestamp_sent,
            'messageId': message_id,
            'status': EmailStatus.SENT.value,
            'user_id': 'dev_123',
            'recipient_name': name,
            'sender_name': sent_from,
            'thread_id': thread_id,
            'email_subject': email_subject,
            'message_id_header':message_id_header

        }
    )
    
    # Save or update the thread in Firestore
    save_thread_to_firestore(thread_id, metadata={
        'last_updated': timestamp_sent,
        'sent_from': sent_from,
        'to_email': email,
        'user_id': 'dev_123',
    })

    # Add the message to the thread's messages subcollection
    add_message_to_thread(thread_id, message_id, {
        'email_body': email_body,
        'email_subject': email_subject,
        'sent_from': sent_from,
        'owner': AgentOwnerStatus.EMAILER.value,
        'to_email': email,
        'slide_filepath': slide_res_filepath,
        'timestamp_sent': timestamp_sent,
        'messageId': message_id,
        'status': EmailStatus.SENT.value,
        'user_id': 'dev_123',
        'recipient_name': name,
        'sender_name': sent_from,
        'email_subject': email_subject,
        # 'message_id_header': message_id_header

    })

    return message_id

 