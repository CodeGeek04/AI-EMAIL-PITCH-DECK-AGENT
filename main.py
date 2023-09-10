from langchain.agents.agent_toolkits import GmailToolkit
from langchain import OpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools.gmail.utils import build_resource_service, get_gmail_credentials

import streamlit as st

def _build_gmail_agent():
    toolkit = GmailToolkit()

    # Can review scopes here https://developers.google.com/gmail/api/auth/scopes
    # For instance, readonly scope is 'https://www.googleapis.com/auth/gmail.readonly'
    credentials = get_gmail_credentials(
        token_file="token.json",
        scopes=["https://mail.google.com/"],
        # client_secrets_file="creds4.json",
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

def email_contacts(input):
    agent = _build_gmail_agent()
    res = agent.run(input)
    return res

def main():
    while True:
        user_input = input("Enter your command: ")
        result = email_contacts(user_input)
        print(result)

# if __name__ == "__main__":
#     main()


st.header("Emailer agent")

user_input = st.text_input("Enter your command")

if st.button("enter"):
    result = email_contacts(user_input)
    st.write(result)