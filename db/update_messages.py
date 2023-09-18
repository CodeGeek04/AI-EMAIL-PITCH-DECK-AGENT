from requests import HTTPError

import firebase_admin
from firebase_admin import firestore
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.prompts import PromptTemplate
import base64
import time
from db.utils import (
    update_message_status_firestore, 
    get_token_from_firestore, 
    update_message_status_and_owner_firestore,
    AgentOwnerStatus,
    EmailStatus
)


def update_status_firestore(message_id, sentiment_status, db):
    message_ref = db.collection('messages').document(message_id)
    message_ref.update({"status": sentiment_status})


def get_email_body_for_message_id(gmail_service, message_id):
    try:
        # Fetch the message details
        message = gmail_service.users().messages().get(userId='me', id=message_id).execute()
        print('email message', message)
        if 'parts' in message['payload']:
            body_data = message['payload']['parts'][0]['body']['data']
            email_body = base64.urlsafe_b64decode(body_data).decode('utf-8')
            return email_body

    except Exception as e:
        print(f"Error fetching email body: {e}")
        return None

def get_email_sentiment(email_body):
    # Existing code for sentiment determination
    determine_sentiment_prompt = """
        Your task is to determine the sentiment of this email response to determine the sentiment of the follwoing email message to see if they are receptive to getting on a call or not.
        Email body: {email_body} 
        ---
        ONLY Answer with the following options and nothing else:
        ---
        IS_RECEPTIVE
        NOT_RECEPTIVE
        ---
        Only output the values either IS_RECEPTIVE or NOT_RECEPTIVE
        Begin!
    """
    human_message_prompt = HumanMessagePromptTemplate.from_template(
            template=determine_sentiment_prompt
        )
    chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])
    prompt = chat_prompt.format_prompt(
            email_body=email_body
        ).to_messages()

    chat = ChatOpenAI(temperature=0)
    result = chat(prompt)
    print('result', result)
    if result.content == 'IS_RECEPTIVE':
        return 'IS_RECEPTIVE'
    elif result.content == 'NOT_RECEPTIVE':
        return 'NOT_RECEPTIVE'
    else:
        return 'ERROR'

def determine_sentiment(gmail_service, message_id):
    email_body = get_email_body_for_message_id(gmail_service, message_id)
    sentiment_result = get_email_sentiment(email_body)
    print('sentiment result', sentiment_result)
    return sentiment_result
    



def get_gmail_service(user_token):
    creds = Credentials(token=user_token['token'],
                        refresh_token=user_token['refresh_token'],
                        token_uri=user_token['token_uri'],
                        client_id=user_token['client_id'],
                        client_secret=user_token['client_secret'],
                        scopes=user_token['scopes'])
    service = build('gmail', 'v1', credentials=creds)
    return service

# def check_for_reply(gmail_service, message_id, to_email):
#     try:
#         # Get the details of the original message
#         original_message = gmail_service.users().messages().get(userId='me', id=message_id).execute()
#         print('origina; message', original_message)
#         # If the message doesn't have a threadId, it's not part of a conversation, so no reply
#         if not original_message.get('threadId'):
#             return False

#         # Get the entire thread using the threadId
#         thread = gmail_service.users().threads().get(userId='me', id=original_message['threadId']).execute()

#         # Extract the latest message from the thread
#         latest_message = thread['messages'][-1]

#         # Fetch the email address of the recipient of the latest message
#         headers = latest_message['payload']['headers']
#         to_header = next(header for header in headers if header["name"] == "To")
#         recipient_email = to_header['value']

#         # If the latest message is to the given email (i.e., our email), then the recipient has replied
#         return to_email in recipient_email

#     except HTTPError as e:
#         print(f"Error checking for reply: {e}")
        # return False
def check_for_reply(gmail_service, message_id, to_email):
    try:
        # Get the details of the original message
        original_message = gmail_service.users().messages().get(userId='me', id=message_id).execute()
        print('Original message', original_message)

        # If the message doesn't have a threadId, it's not part of a conversation, so no reply
        thread_id = original_message.get('threadId')
        if not thread_id:
            return False

        # Get the entire thread using the threadId
        thread = gmail_service.users().threads().get(userId='me', id=thread_id).execute()

        # Check all messages in the thread after the original for a reply
        messages = thread.get('messages', [])
        for message in messages:
            # Skip the original message
            if message['id'] == message_id:
                continue
            
            # Check the sender of the message
            headers = message['payload']['headers']
            from_header = next((header for header in headers if header["name"] == "From"), None)
            if from_header and to_email in from_header['value']:
                return True

        return False

    except Exception as e:
        print(f"Error checking for reply: {e}")
        return False


def update_messages(messages):
    # Initialize Firebase Admin SDK (do this once for your app)
  # Initialize Firestore client

    for message_data in messages:
        user_id = message_data.get('user_id')
        message_id = message_data.get('messageId')
        to_email = message_data.get('to_email')

        # Ensure you have all the necessary data for each message
        if not user_id or not message_id or not to_email:
            print(f"Skipping message due to missing data: {message_data}")
            continue

        # Fetch user token
        user_token_doc = get_token_from_firestore(user_id=user_id)
        if not user_token_doc:
            print(f"Token for user {user_id} not found!")
            continue

        user_token = user_token_doc

        # Get Gmail Service
        gmail_service = get_gmail_service(user_token)
        print('gmail_service', gmail_service)
        # Check for reply
        has_reply = check_for_reply(gmail_service=gmail_service, message_id=message_id, to_email=to_email)
        print('hasreply', has_reply)
        if has_reply:
            sentiment_status = determine_sentiment(
                gmail_service=gmail_service,
                message_id=message_id,
            )

            if sentiment_status == 'IS_RECEPTIVE':
                update_message_status_and_owner_firestore(
                    message_id=message_id, 
                    new_status=EmailStatus.READY_TO_SCHEDULE.value,
                    owner_status=AgentOwnerStatus.SCHEDULER.value
                    )
            elif sentiment_status == 'NOT_RECEPTIVE':
                update_message_status_firestore(
                    message_id=message_id, 
                    new_status=EmailStatus.DISENGAGED.value
                )
            else:
                # Handle any other states if necessary
                print(f"Unexpected sentiment status for message {message_id}: {sentiment_status}")

    print('Message update completed successfully')