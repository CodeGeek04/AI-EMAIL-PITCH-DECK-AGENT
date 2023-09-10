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
from elysium_prompts.email_prompts.email_body_prompts import elysium_email_body_template_investor_outreach
from db.utils import get_token_from_db
import json
import os

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
        sent_from: str = "Michael"
    ):
    _generate_token_file()
    agent = _build_gmail_agent()
    prompt_template = PromptTemplate.from_template(template=elysium_email_body_template_investor_outreach)
    formatted = prompt_template.format(recipient_name=name, email=email, entity_name=entity, sent_from=sent_from)
    query = f"Write a Gmail draft to {name} to their email: {email}. Make it personalized based on the fact that you know they work at {entity}"
    agent.run(formatted)
    _clean_up_token_file()

