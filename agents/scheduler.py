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

from elysium_prompts.deck_prompts.pitch_deck_prompts import pitch_content
from elysium_prompts.email_prompts.email_subject_prompts import elysium_email_subject_template_1
from elysium_prompts.email_prompts.email_body_prompts_manual import elysium_email_body_template_investor_outreach_v2, elysium_shceduler_prompt_initial
# from agents.gmail_agent_v2 import generate_email_body
from db.utils import (
    AgentOwnerStatus, 
    EmailStatus, 
    get_token_from_db, 
    save_message_metadata_to_firestore, 
    get_firebase_credentials_from_env, 
    update_message_status_and_owner_firestore,
    get_thread_from_firestore,
    save_thread_to_firestore,
    add_message_to_thread,
    get_token_from_firestore
    )
import json
import os


from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import base64
from email.mime.text import MIMEText
from constants.hermes_scheduler import HERMES_EMAIL

def create_message(sender, to, subject, message_text, message_id_header, thread_id):
    print(f"Sender: {sender}")

    """Create a message for an email."""
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = HERMES_EMAIL
    message['cc'] = sender
    message['Subject'] = subject
    if message_id_header:
        message['In-Reply-To'] = message_id_header
        message['References'] = message_id_header

    # message['subject'] = subject
    # print(message)
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}
    if thread_id:
        return {'raw': raw_message, 'threadId': thread_id}
    else:
        return {'raw': raw_message}

def send_email(service, user_id, message):
    """Send an email through the Gmail API."""
    try:
        sent_message = service.users().messages().send(
            userId=user_id, body=message
        ).execute()
        print(f"Message sent: {sent_message['id']}")
        return sent_message
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def get_gmail_service():
    from oauth2client.service_account import ServiceAccountCredentials

    # Use your function to get Firebase credentials
    firebase_creds = get_firebase_credentials_from_env()
    print(firebase_creds.get('client_id'))
    # Create service account credentials
    # credentials = ServiceAccountCredentials.from_json_keyfile_dict(firebase_creds, scopes=['https://www.googleapis.com/auth/gmail.send'])

    # # Impersonate the desired user
    # delegated_credentials = credentials.create_delegated('hermes@elysiuminnovations.ai')
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    # Create service account credentials
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(firebase_creds, scopes=SCOPES)
    delegated_credentials = credentials.create_delegated('hermes@elysiuminnovations.ai')

    # Impersonate the desired user
    # Build the Gmail service
    service = build('gmail', 'v1', credentials=delegated_credentials)
    
    return service



def get_user_service(user_id, service_name='gmail', version='v1'):
    token_data = get_token_from_firestore(user_id)

    # Create credentials object
    creds = Credentials(
        token=token_data['token'],       
        refresh_token=token_data['refresh_token'],
        token_uri=token_data['token_uri'],
        client_id=token_data['client_id'],
        client_secret=token_data['client_secret'],
        scopes=token_data['scopes']
    )

    # Build the Google Calendar service
    service = build(service_name, version, credentials=creds)
    return service

def get_schedule(user_id):
    from dateutil import parser

    # Build the Google Calendar service
    service = get_user_service(user_id=user_id, service_name='calendar', version='v3')

    # Define the time frame for which you want to fetch events. For example, fetching events for the next 7 days:
    # (You can modify this as per your requirements)
    import datetime
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    end_time = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat() + 'Z'

    # Fetch events
    events_result = service.events().list(
        calendarId='primary', 
        timeMin=now, 
        timeMax=end_time, 
        singleEvents=True,
    orderBy='startTime').execute()

    
    events = events_result.get('items', [])
    # for event in events:
    #     if 'dateTime' in event['start']:
    #         start_time_event = event['start']['dateTime']
    #         if isinstance(start_time_event, str):
    #             event['start']['dateTime'] = parser.parse(start_time_event)

    #     if 'dateTime' in event['end']:
    #         end_time_event = event['end']['dateTime']
    #         if isinstance(end_time_event, str):
    #             event['end']['dateTime'] = parser.parse(end_time_event)


    # Return the events or process them as required
    return events





from datetime import datetime, timedelta, time
import dateutil.parser
import pytz

def get_free_slots(events, days_out=3):

    local_timezone = pytz.timezone('America/New_York')  # Adjust this to your local timezone
    current_date = datetime.now(local_timezone)
    start_date = current_date + timedelta(days=2)
    end_date = start_date + timedelta(days=days_out-1)
   
    
    # Create a list for the entire time range, initialized as free (True)
    hours = [True] * 24 * days_out

    # Parse events and mark occupied slots
    for event in events:
        start_time = dateutil.parser.parse(event['start']['dateTime'])
        end_time = dateutil.parser.parse(event['end']['dateTime'])
        
        if start_date.date() <= start_time.date() <= end_date.date():
            start_hour = (start_time - start_date).seconds // 3600 + (start_time - start_date).days * 24
            end_hour = (end_time - start_date).seconds // 3600 + (end_time - start_date).days * 24

            for i in range(start_hour, end_hour):
                hours[i] = False

    # Extract continuous free slots
    free_slots = []
    start_hour = None
    for i, free in enumerate(hours):
        if free and start_hour is None:
            start_hour = i
        elif not free and start_hour is not None:
            end_hour = i
            free_slots.append((start_date + timedelta(hours=start_hour), start_date + timedelta(hours=end_hour)))
            start_hour = None
    if start_hour is not None:
        free_slots.append((start_date + timedelta(hours=start_hour), start_date + timedelta(hours=len(hours))))
    
    return free_slots


def get_free_slots_v2(events, days_out=3):

    local_timezone = pytz.timezone('America/New_York')  # Adjust this to your local timezone
    current_date = datetime.now(local_timezone)
    
    # Adjust the start date to skip weekends
    start_date = current_date
    while start_date.weekday() >= 5 or start_date.date() == current_date.date():  # 5 is Saturday, 6 is Sunday
        start_date += timedelta(days=1)

    end_date = start_date
    days_added = 0
    while days_added < days_out:
        if end_date.weekday() < 5:  # Exclude weekends
            days_added += 1
        end_date += timedelta(days=1)

    # Create a list for the entire time range, initialized as free (True)
    total_hours = (end_date - start_date).days * 24
    hours = [True] * total_hours * 2  # Multiplied by 2 to check every half-hour

    # Parse events and mark occupied slots
    for event in events:
        start_time = dateutil.parser.parse(event['start']['dateTime'])
        end_time = dateutil.parser.parse(event['end']['dateTime'])
        
        # Make sure the times are within our desired range
        if start_time < start_date:
            start_time = start_date
        if end_time > end_date:
            end_time = end_date

        if start_date.date() <= start_time.date() <= end_date.date():
            start_half_hour = 2 * ((start_time - start_date).seconds // 3600 + (start_time - start_date).days * 24)
            end_half_hour = 2 * ((end_time - start_date).seconds // 3600 + (end_time - start_date).days * 24)

            for i in range(start_half_hour, end_half_hour):
                # Add a safety check to avoid IndexError
                if i < len(hours):
                    hours[i] = False

    # Extract 30-minute free slots
    free_slots = []
    # for i in range(0, len(hours) - 1, 2):  # Step of 2 to check for 30-minute intervals
    #     hour_of_day = (i // 2) % 24
    #     if 9 <= hour_of_day < 21:  # Only consider times between 9 AM and 9 PM
    #         if hours[i] and hours[i + 1]:  # Check for 30-minute free interval
    #             start_time = start_date + timedelta(hours=hour_of_day)
    #             end_time = start_time + timedelta(minutes=30)
    #             free_slots.append((start_time, end_time))
    for i in range(0, len(hours) - 1, 2):  # Step of 2 to check for 30-minute intervals
        hour_of_day = (i // 2) % 24
        if 9 <= hour_of_day < 21:  # Only consider times between 9 AM and 9 PM
            if hours[i] and hours[i + 1]:  # Check for 30-minute free interval
                start_time = start_date + timedelta(hours=hour_of_day)
                if (i % 48) != 46:  # To ensure we don't cross the day boundary
                    end_time = start_time + timedelta(minutes=30)
                    free_slots.append((start_time, end_time))

    
    return free_slots

def get_free_slots_v3(current_time, events, duration_minutes=30, days_to_check=3):
    slots = []
    
    # Define the start and end times
    start_time = time(9, 0)
    end_time = time(21, 0)
    
    # Convert events to datetime objects for easier comparison
    existing_events = []
    for event in events:
        start_time_event = dateutil.parser.parse(event['start']['dateTime'])
        end_time_event = dateutil.parser.parse(event['end']['dateTime'])
        existing_events.append((start_time_event, end_time_event))
    
    # Generate all potential slots for the desired days
    for day in range(days_to_check):
        current_date = current_time.date() + timedelta(days=day)
        
        # On the first day, we start from the next half-hour mark or the given start time, whichever is later
        if day == 0:
            if current_time.time() < start_time:
                slot_start = datetime.combine(current_date, start_time)
            else:
                next_half_hour = (current_time.minute // 30 + 1) * 30
                if next_half_hour == 60:
                    next_hour = current_time.hour + 1
                    next_half_hour = 0
                else:
                    next_hour = current_time.hour
                slot_start = datetime.combine(current_date, time(next_hour, next_half_hour))
        else:
            slot_start = datetime.combine(current_date, start_time)
        
        # Generate the slots for the day
        while slot_start.time() < end_time:
            slot_end = slot_start + timedelta(minutes=duration_minutes)
            if slot_end.time() > end_time:
                break
            
            # Convert the slots to UTC for comparison
            utc_timezone = pytz.UTC
            slot_start_utc = slot_start.astimezone(utc_timezone)
            slot_end_utc = slot_end.astimezone(utc_timezone)
            
            # Check if the slot conflicts with existing events
            slot_conflicts = any(
                (event_start <= slot_start_utc < event_end) or 
                (event_start < slot_end_utc <= event_end) or 
                (slot_start_utc <= event_start < slot_end_utc) or 
                (slot_start_utc < event_end <= slot_end_utc)
                for event_start, event_end in existing_events
            )
            
            if not slot_conflicts:
                slots.append((slot_start, slot_end))
            
            slot_start = slot_end
    
    return slots

def get_free_slots_v4(current_time, events, duration_minutes=30, days_to_check=3):
    slots = []
    
    # Define the start and end times
    start_time = time(9, 0)
    end_time = time(21, 0)
    
    # Convert events to datetime objects for easier comparison
    existing_events = []
    for event in events:
        start_time_event = dateutil.parser.parse(event['start']['dateTime'])
        end_time_event = dateutil.parser.parse(event['end']['dateTime'])
        existing_events.append((start_time_event, end_time_event))
    
    days_checked = 0
    while days_checked < days_to_check:
        current_date = current_time.date() + timedelta(days=days_checked)

        # If the current_date is a weekend, skip to the next day
        if current_date.weekday() >= 5:  # 5 is Saturday, 6 is Sunday
            current_time += timedelta(days=1)
            continue

        days_checked += 1
        
        # On the first day, we start from the next half-hour mark or the given start time, whichever is later
        if days_checked == 1:
            if current_time.time() < start_time:
                slot_start = datetime.combine(current_date, start_time)
            else:
                next_half_hour = (current_time.minute // 30 + 1) * 30
                if next_half_hour == 60:
                    next_hour = current_time.hour + 1
                    next_half_hour = 0
                else:
                    next_hour = current_time.hour
                slot_start = datetime.combine(current_date, time(next_hour, next_half_hour))
        else:
            slot_start = datetime.combine(current_date, start_time)
        
        # Generate the slots for the day
        while slot_start.time() < end_time:
            slot_end = slot_start + timedelta(minutes=duration_minutes)
            if slot_end.time() > end_time:
                break
            
            # Convert the slots to UTC for comparison
            utc_timezone = pytz.UTC
            slot_start_utc = slot_start.astimezone(utc_timezone)
            slot_end_utc = slot_end.astimezone(utc_timezone)
            
            # Check if the slot conflicts with existing events
            slot_conflicts = any(
                (event_start <= slot_start_utc < event_end) or 
                (event_start < slot_end_utc <= event_end) or 
                (slot_start_utc <= event_start < slot_end_utc) or 
                (slot_start_utc < event_end <= slot_end_utc)
                for event_start, event_end in existing_events
            )
            
            if not slot_conflicts:
                slots.append((slot_start, slot_end))
            
            slot_start = slot_end
    
    return slots


    
def generate_email_scheduler_body(
        sender_name: str,
        recipient_name: str,
        selected_body_prompt: str,
        schedule
    ):
    human_message_prompt = HumanMessagePromptTemplate.from_template(
            template=selected_body_prompt
        )
    chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])
    prompt = chat_prompt.format_prompt(
            sender_name=sender_name,
            recipient_name=recipient_name,
            schedule=schedule
        ).to_messages()

    chat = ChatOpenAI(temperature=0)
    result = chat(prompt)
   
    return result.content

def get_thread(service, thread_id):
    """
    Retrieve a thread from Hermes's inbox using its threadId.

    Parameters:
    - service: An authenticated Gmail API service instance.
    - thread_id: The ID of the thread to be retrieved.

    Returns:
    - thread: The entire thread (including all individual messages) as a dictionary.
             If the thread is not found or an error occurs, it returns None.
    """
    try:
        thread = service.users().threads().get(userId='me', id=thread_id).execute()
        return thread
    except Exception as e:
        print(f"An error occurred while retrieving thread {thread_id}: {e}")
        return None

def run_scheduler_agent(messages):
    for message in messages:
        user_id = message.get('user_id')
        email_body = message.get('email_body')
        email_subject = message.get('email_subject')
        sent_from = message.get('sent_from')
        to_email = message.get('to_email')
        slide_filepath = message.get('slide_filepath')
        timestamp_sent = message.get('timestamp_sent')
        message_id = message.get('messageId')
        status = message.get('status')
        owner = message.get('owner')
        recipient_name = message.get('recipient_name')
        sender_name = message.get('sender_name')
        thread_id = message.get('thread_id')
        message_id_header = message.get('message_id_header')
        message_subject = message.get('email_subject')
        
        # Check if user_id exists before proceeding
        if not user_id:
            print(f"User ID missing for message {message.get('message_id')}. Skipping...")
            continue

        # Get the user's schedule
        user_schedule = get_schedule(user_id)
        local_timezone = pytz.timezone('America/New_York')  # Adjust this to your local timezone
        current_time = datetime.now(local_timezone)

        # Get free slots for the user considering existing events in their schedule
        free_slots = get_free_slots_v4(current_time, user_schedule)
        # for slot in free_slots:
        #     print(slot[0].strftime('%B %d, %Y %I:%M %p') + " - " + slot[1].strftime('%I:%M %p'))

        print('user schedule', free_slots)
        service = get_user_service(user_id=user_id)
    
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile['emailAddress']

        email_body = generate_email_scheduler_body(
            sender_name=sender_name,
            selected_body_prompt=elysium_shceduler_prompt_initial,
            recipient_name=recipient_name,
            schedule=free_slots
        )

        # print('email body', email_body)
        print('thread_id', thread_id)
        email_subject = f"Scheduling a call for {recipient_name}"
        raw_email = create_message(
            sender=email_address, 
            to=to_email, 
            subject=message_subject, 
            message_text=email_body, 
            # message_id=message_id,
            message_id_header=message_id_header,
            thread_id=thread_id
        )
        print('raw email', raw_email)
        response = send_email(
            get_gmail_service(), 
            'me', 
            raw_email,
        )
        if response:
            sent_message_id = response['id']

            # Create and save the new message metadata to Firestore
            new_message_metadata = {
                "messageId": sent_message_id,
                "thread_id": thread_id,
                "status": EmailStatus.SCHEDULE_SENT.value,
                "owner": AgentOwnerStatus.SCHEDULER.value,
                "sent_from": email_address,
                "to_email": to_email,
                "email_subject": email_subject,
                "email_body": email_body,
                "timestamp_sent": datetime.utcnow().isoformat()
            }
            save_message_metadata_to_firestore(sent_message_id, new_message_metadata)

            # Check if the thread exists in Firestore
            existing_thread = get_thread_from_firestore(thread_id)
            if not existing_thread:
                # If thread doesn't exist, create a new thread in Firestore
                save_thread_to_firestore(thread_id, {"initial_message_id": message_id})

            # Add the new message to the thread's subcollection of messages in Firestore
            add_message_to_thread(thread_id, sent_message_id, new_message_metadata)

# ============== # PHASE 2 In Scheduler ============== #

def schedule_google_calendar_event(
        event_title, 
        date, 
        time, 
        recipient_email
):
    def convert_to_24_hour_format(time_str):
        try:
            # Try to parse the time string as 12-hour format
            dt_obj = datetime.strptime(time_str, '%I:%M %p')
            return dt_obj.strftime('%H:%M')
        except ValueError:
            try:
                # If above fails, try to parse the time string as 24-hour format
                dt_obj = datetime.strptime(time_str, '%H:%M')
                return dt_obj.strftime('%H:%M')
            except ValueError:
                # If both formats fail, raise an error
                raise ValueError(f"Invalid time format: {time_str}")
    # Load your saved user credentials or authenticate if running for the first time
    service = get_user_service(user_id='dev_123', service_name='calendar', version='v3')
    time_24hr = convert_to_24_hour_format(time)

    # hour, minute = time.split(":")
    # padded_time = f"{hour.zfill(2)}:{minute}"

    # Convert date and time to RFC3339 format
    start_time_str = f"{date}T{time_24hr}:00"
    start_time = datetime.fromisoformat(start_time_str).astimezone(pytz.utc)
    end_time = start_time + timedelta(hours=1)  # Assuming 1 hour duration for simplicity


    event = {
        'summary': event_title,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'UTC',
        },
        'attendees': [
            {'email': recipient_email}
        ],
        'conferenceData': {
            'createRequest': {
                'requestId': 'hangoutsMeet'  # This will create a Google Meet link
            }
        }
    }

    event_result = service.events().insert(calendarId='primary', body=event, conferenceDataVersion=1).execute()
    print(event_result)
    return event_result.get('htmlLink')

def extract_calendar_args_and_handle_call(
        response_content,
        recipient_email
):
    import openai
    functions = [
        {
            "name": "schedule_google_calendar_event",
            "description": "Schedule an event on Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_title": {
                        "type": "string",
                        "description": "The title of the event."
                    },
                    "date": {
                        "type": "string",
                        "description": "The date of the event in YYYY-MM-DD format."
                    },
                    "time": {
                        "type": "string",
                        "description": "The time of the event in HH:MM format."
                    },
                    # ... any other relevant details like duration, attendees, etc.
                },
                "required": ["event_title", "date", "time"]
            }
        }
    ]
    messages = [{"role": "user", "content": f"Schedule a google calendar event based on the following response email: \n {response_content}"}]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        functions=functions,
        function_call="auto"
    )
    response_message = response["choices"][0]["message"]

    if response_message.get("function_call"):
        available_functions = {
            "schedule_google_calendar_event": schedule_google_calendar_event,
        } 
        print(response_message)
        function_name = response_message["function_call"]["name"]
        fuction_to_call = available_functions[function_name]

        function_args = json.loads(response_message["function_call"]["arguments"])
        event_title = function_args.get("event_title")
        date = function_args.get("date")
        time = function_args.get("time")
        function_response = fuction_to_call(
            event_title=function_args.get("event_title"),
            date=function_args.get("date"),
            time=time,
            recipient_email=recipient_email
        )
        return function_response


def analyze_response_content(response_content):
    print('response content: =========\n', response_content)
    from elysium_utils.output_parsers import get_calendar_date_parser
    # Existing code for sentiment determination
    determine_sentiment_prompt = """
        You are an AI Scheduler Assistant and have rceeived a response from the recipient after we sent them available times for use to call. 
        Your goal is to determine wether the recipient said they can make any of the times we sent as available or if they need more times.
        Here is the recpient's response:
        ---
        {recipient_response}
        ---
        You must determine whether the recipient confirmed a time we suggested to them or if they need more times suggested. If they confirmed a time you will answer with CONFIRMED_TIME and if they need a new time you will answer with NEEDS_NEW_TIME.
        Again, the only options you have to respond with are:
        ---
        NEEDS_NEW_TIME
        CONFIRMED_TIME
        ---
        Begin!
    """
    human_message_prompt = HumanMessagePromptTemplate.from_template(
            template=determine_sentiment_prompt
        )
    chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])
    prompt = chat_prompt.format_prompt(
            recipient_response=response_content
        ).to_messages()

    chat = ChatOpenAI(temperature=0)
    result = chat(prompt)
    print('result', result)
    return result.content

def get_latest_response(thread_data, sent_from):
    """
    Extracts the latest response from the Gmail thread.

    Parameters:
    - thread_data: The entire thread data retrieved from Gmail.
    - sent_from: Email address of the sender to distinguish between sent and received messages.

    Returns:
    - Latest response message or None if no response is found.
    """
    messages = thread_data.get('messages', [])
    messages.reverse()  # We reverse the list to start from the latest message
    
    for message in messages:
        # Check if the message is from the recipient (i.e., not sent by us)
        headers = message['payload'].get('headers', [])
        from_header = next((header for header in headers if header['name'] == 'From'), None)
        
        if from_header and sent_from not in from_header['value']:
            # Decoding the message body
            raw_data = message['payload']['body'].get('data', '')
            body_data = base64.urlsafe_b64decode(raw_data).decode('utf-8').strip()
            
            # If body_data is empty, try to get the content from the 'parts' field
            if not body_data:
                parts = message['payload'].get('parts', [])
                for part in parts:
                    if part['mimeType'] == 'text/plain':  # We are focusing on plain text content
                        body_data = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8').strip()
                        break

            return {
                'body': body_data,
                'date': message['internalDate']
            }
    return None


# PHASE 2 In Scheduler
def process_scheduler_messages(messages):
    hermes_gmail_service = get_gmail_service()

    for message in messages:
        user_id = message.get('user_id')
        email_body = message.get('email_body')
        email_subject = message.get('email_subject')
        sent_from = message.get('sent_from')
        to_email = message.get('to_email')
        slide_filepath = message.get('slide_filepath')
        timestamp_sent = message.get('timestamp_sent')
        message_id = message.get('messageId')
        status = message.get('status')
        owner = message.get('owner')
        recipient_name = message.get('recipient_name')
        sender_name = message.get('sender_name')
        thread_id = message.get('thread_id')
        message_id_header = message.get('message_id_header')
        message_subject = message.get('email_subject')
        # print(message)
        service = get_user_service(user_id='dev_123')
        thread_data = get_thread(service, thread_id)
        # print(thread_data)
        if not thread_data:
            print(f"Thread with ID {thread_id} not found in user's inbox. Skipping...")
            continue

        # 2. Parse the thread for a new response
        response_message = get_latest_response(thread_data, sent_from)  # Assuming the function `get_latest_response` extracts the latest response from the thread
        if not response_message:
            print(f"No response found for message with ID {message_id}. Skipping...")
            continue

        # 3. Analyze the content of the response
        print('response message', response_message)
        response_content = response_message['body']
        response_analysis = analyze_response_content(response_content)
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile['emailAddress']
        if response_analysis == 'CONFIRMED_TIME':
            extracted_date_time = extract_calendar_args_and_handle_call(
                response_content=response_content,
                recipient_email=to_email
            )
            
            raw_email = create_message(
                sender=email_address, 
                to=to_email, 
                subject=message_subject, 
                message_text=f'Meeting confirmed! \n {extracted_date_time}', 
                message_id_header=message_id_header,
                thread_id=thread_id
            )
            print('raw email', raw_email)
            response = send_email(
                get_gmail_service(), 
                'me', 
                raw_email,
            )
            success = update_message_status_and_owner_firestore(
                message_id=message_id,
                new_status=EmailStatus.SCHEDULED.value,
                owner_status=AgentOwnerStatus.SCHEDULER.value
            )
            return { status: 200, message_id: message_id }
        if response_analysis == 'NEEDS_NEW_TIME':
            print("NEED TO SEND NEW TIMES!")
            elysium_calendly = "https://calendly.com/0xmerk/30min"
            raw_email = create_message(
                sender=email_address, 
                to=to_email, 
                subject=message_subject, 
                message_text=f'It appears my suggested times are not convenient. Please find another time that works for you here: {elysium_calendly}', 
                message_id_header=message_id_header,
                thread_id=thread_id
            )
            print('raw email', raw_email)
            response = send_email(
                get_gmail_service(), 
                'me', 
                raw_email,
            )
            pass
        # # 4. Update the status in Firestore based on the analysis
        # if availability:
        #     update_message_status_and_owner_firestore(
        #         message_id=message_id,
        #         new_status=EmailStatus.MEETING_SCHEDULED.value,
        #         owner_status=AgentOwnerStatus.SCHEDULER.value
        #     )
        # else:
        #     update_message_status_and_owner_firestore(
        #         message_id=message_id,
        #         new_status=EmailStatus.FURTHER_ACTION_NEEDED.value,
        #         owner_status=AgentOwnerStatus.SCHEDULER.value
        #     )






# def extract_date_time(response_content):
#     from langchain.chains import create_extraction_chain
#     from elysium_utils.output_parsers import get_calendar_date_parser
#     # Schema    
#     schema = {
#         "properties": {
#             "date": {"type": "string"},
#             "day": {"type": "integer"},
#             "time": {"type": "string"},
#         },
#         "required": ["day", "time"],
#     }

#     # Input 
    

#     # Run chain
#     llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
#     chain = create_extraction_chain(schema, llm)
#     res = chain.run(response_content)
#     print(res)
#     model_name = "text-davinci-003"
#     temperature = 0.0
#     model = OpenAI(model_name=model_name, temperature=temperature)
#     calendar_parser = get_calendar_date_parser()
#     calendar_prompt = PromptTemplate(
#         template="Extract the date and time from the recipeint's response.\n{format_instructions}\n{response}\n",
#         input_variables=["response"],
#         partial_variables={"format_instructions": calendar_parser.get_format_instructions()},
#     )
#     _input = calendar_prompt.format_prompt(query=response_content)
#     output = model(_input.to_string())
#     parsed_output = calendar_parser.parse(output)
#     return parsed_output
