import json
TOKEN_DB_PATH = 'token_db.json'
MESSAGE_ID_DB_PATH = 'message_ids_db.json'

def save_token_to_db(user_id, token_data):
    """Save token data to a local JSON file."""
    try:
        with open(TOKEN_DB_PATH, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    data[user_id] = token_data

    with open(TOKEN_DB_PATH, 'w') as f:
        json.dump(data, f)



def get_token_from_db(user_id):
    """Retrieve token data for a user from the local JSON file."""
    try:
        with open(TOKEN_DB_PATH, 'r') as f:
            data = json.load(f)
            return data.get(user_id)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    

def save_message_metadata(user_id, message_id, metadata):
    try:
        with open(MESSAGE_ID_DB_PATH, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    user_data = data.get(user_id, {})
    user_data[message_id] = metadata
    data[user_id] = user_data

    with open(MESSAGE_ID_DB_PATH, 'w') as f:
        json.dump(data, f)


def update_message_status(user_id, message_id, new_status):
    with open(MESSAGE_ID_DB_PATH, 'r') as f:
        data = json.load(f)

    if user_id in data and message_id in data[user_id]:
        data[user_id][message_id]["status"] = new_status

        with open(MESSAGE_ID_DB_PATH, 'w') as f:
            json.dump(data, f)

def get_message_metadata(user_id, message_id):
    try:
        with open(MESSAGE_ID_DB_PATH, 'r') as f:
            data = json.load(f)
            return data[user_id].get(message_id)
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


def get_messages_by_status(user_id, status):
    try:
        with open(MESSAGE_ID_DB_PATH, 'r') as f:
            data = json.load(f)
            user_data = data.get(user_id, {})
            return [msg_id for msg_id, metadata in user_data.items() if metadata["status"] == status]
    except (FileNotFoundError, json.JSONDecodeError):
        return []



# FIRESTORE IMPLEMENTATION
from enum import Enum
import datetime

class EmailStatus(Enum):
    # Phase 1: Emailer Agent
    SENT = "SENT"
    REPLIED = "REPLIED"
    PASSED_TO_SCHEDULER = "PASSED_TO_SCHEDULER"
    DISENGAGED = "DISENGAGED"
    # Phase 2: Scheduler Agent
    READY_TO_SCHEDULE = "READY_TO_SCHEDULE"
    SCHEDULE_SENT = "SCHEDULE_SENT"
    SCHEDULED = "SCHEDULED"
    NEEDS_REPLY = "NEEDS_REPLY"
    NEEDS_FOLLOW_UP = "NEEDS_FOLLOW_UP"
    RESCHEDULE_REQUESTED = "RESCHEDULE_REQUESTED"
    CANCELLED = "CANCELLED"

class AgentOwnerStatus(Enum):
    EMAILER = 'EMAILER'
    SCHEDULER = 'SCHEDULER'


import os
import firebase_admin
from firebase_admin import credentials, firestore

def get_firebase_credentials_from_env():
    return {
        "type": os.environ["FIREBASE_TYPE"],
        "project_id": os.environ["FIREBASE_PROJECT_ID"],
        "private_key_id": os.environ["FIREBASE_PRIVATE_KEY_ID"],
        "private_key": os.environ["FIREBASE_PRIVATE_KEY"].replace("\\n", "\n"),
        "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
        "client_id": os.environ["FIREBASE_CLIENT_ID"],
        "auth_uri": os.environ["FIREBASE_AUTH_URI"],
        "token_uri": os.environ["FIREBASE_TOKEN_URI"],
        "auth_provider_x509_cert_url": os.environ["FIREBASE_AUTH_PROVIDER_X509_CERT_URL"],
        "client_x509_cert_url": os.environ["FIREBASE_CLIENT_X509_CERT_URL"]
    }

firebase_cred = credentials.Certificate(get_firebase_credentials_from_env())
firebase_admin.initialize_app(firebase_cred)
db = firestore.client()

def save_token_to_firestore(user_id, token_data):
    tokens_ref = db.collection('tokens')
    tokens_ref.document(user_id).set(token_data)

def get_token_from_firestore(user_id):
    token_ref = db.collection('tokens').document(user_id)
    token = token_ref.get()
    if token.exists:
        return token.to_dict()
    return None

def save_message_metadata_to_firestore(message_id, metadata):
    """Save message metadata to Firestore."""
    message_ref = db.collection('messages').document(message_id)
    message_ref.set(metadata)

def update_message_status_firestore(message_id, new_status):
    """Update the status of a message in Firestore."""
    message_ref = db.collection('messages').document(message_id)
    message_ref.update({"status": new_status})

def get_message_metadata_firestore(message_id):
    """Retrieve metadata of a specific message from Firestore."""
    message_ref = db.collection('messages').document(message_id)
    message_data = message_ref.get()
    if message_data.exists:
        return message_data.to_dict()
    return None

def get_all_messages():
    """Retrieve all messages from Firestore."""
    messages_ref = db.collection('messages')
    messages_data = messages_ref.stream()
    return {message.id: message.to_dict() for message in messages_data}

def update_message_status_and_owner_firestore(message_id, new_status, owner_status):
    """Update the status and owner of a message in Firestore."""
    message_ref = db.collection('messages').document(message_id)
    message_ref.update({
        "status": new_status,
        "owner": owner_status
    })
def save_thread_to_firestore(thread_id, metadata=None):
    """Save a new thread or update an existing thread in Firestore."""
    thread_ref = db.collection('threads').document(thread_id)
    if not metadata:
        metadata = {}  # Default metadata
    thread_ref.set(metadata, merge=True)  # merge=True will ensure that it updates the thread if it exists

def get_thread_from_firestore(thread_id):
    """Retrieve a thread by its ID from Firestore."""
    thread_ref = db.collection('threads').document(thread_id)
    thread_data = thread_ref.get()
    if thread_data.exists:
        return thread_data.to_dict()
    return None

def add_message_to_thread(thread_id, message_id, message_data):
    """Add a message to a thread's subcollection of messages in Firestore."""
    message_ref = db.collection('threads').document(thread_id).collection('messages').document(message_id)
    message_ref.set(message_data)

def get_messages_from_thread(thread_id):
    """Retrieve all messages from a thread's subcollection in Firestore."""
    messages_ref = db.collection('threads').document(thread_id).collection('messages')
    messages_data = messages_ref.stream()
    return {message.id: message.to_dict() for message in messages_data}

def get_all_threads():
    """Retrieve all threads from Firestore."""
    threads_ref = db.collection('threads')
    threads_data = threads_ref.stream()
    return {thread.id: thread.to_dict() for thread in threads_data}
