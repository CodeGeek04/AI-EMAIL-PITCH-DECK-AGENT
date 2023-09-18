from flask import Flask, redirect, request, session, url_for, jsonify
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import os
import json
from datetime import datetime
import uuid  
import csv
from werkzeug.utils import secure_filename

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = 'some_secret_key'



TOKEN_DB_PATH = 'token_db.json'

# ====
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
    

# === files

CSV_MANDATORY_COLUMNS = ['name', 'email','entity']
DATABASE_PATH = 'db.json'
UPLOAD_FOLDER = './uploads'

def preprocess_row(row):
    """Validates and preprocesses a single CSV row."""
    if not all(column in row for column in CSV_MANDATORY_COLUMNS):
        raise ValueError("The row does not conform to the expected format.")
    
    # Normalize data
    row['email'] = row['email'].strip().lower()

    return row

def save_to_db(data):
    """Saves the contacts to the JSON database."""
    job = {
        'contacts': data,
    }

    with open(DATABASE_PATH, 'r') as f:
        db_data = json.load(f)

    db_data.append(job)

    with open(DATABASE_PATH, 'w') as f:
        json.dump(db_data, f)

def process_csv(filepath):
    """Processes the CSV file one row at a time."""
    processed_data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            cleansed_row = preprocess_row(row)
            processed_data.append(cleansed_row)

    return processed_data

@app.route('/upload', methods=['POST'])
def upload():

    file = request.files['csv']
    if not file:
        return "No file uploaded", 400
    # Generate a unique filename
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Process the saved CSV file
    processed_data = process_csv(filepath)
    
    # Save the processed data to the makeshift JSON database
    save_to_db(processed_data)
    os.remove(filepath)

    return "Successfully uploaded and processed the data!"

@app.route('/trigger-email-agent', methods=['POST'])
def trigger_email_agent():
    from agents.gmail_agent import run_email_agent
    from agents.gmail_agent_v2 import run_email_agent_v2
    file = request.files['csv']

    # Process the provided CSV file
    if not file:
        return "No file uploaded", 400
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    # Generate a unique filename
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    file.save(filepath)

    
    # Process the saved CSV file
    print("processing")
    processed_data = process_csv(filepath)

    # Trigger the email agent for each contact
    for contact in processed_data:
        name = contact['name']
        email = contact['email']
        entity = contact['entity']
        website = contact['website'] 
        print('contact', contact)
        run_email_agent_v2(
            name=name,
            email=email,
            entity=entity,
            sent_from="Michael",
            entity_website=website
        )
        
    return jsonify({"status": "success", "message": "Emailer messaged successfully"})


@app.route('/trigger-scheduler',methods=['POST'])
def trigger_scheduler():
    from agents.scheduler import run_scheduler_agent
    messages = request.json.get('messages', [])
    response = run_scheduler_agent(messages=messages)
    return jsonify({"status": "success", "message": "Scheduler triggered successfully"})



@app.route('/update_messages', methods=["POST"])
def update_messages():
    from db.update_messages import update_messages
    messages = request.json.get('messages', [])
    response = update_messages(messages=messages)
    return jsonify({"status": "success", "message": "Messages updated successfully"})

@app.route('/process_scheduled_messages', methods=['POST'])
def process_scheduled_messages():
    from agents.scheduler import process_scheduler_messages

    data = request.get_json()
    messages = data.get('messages', [])

    # Call your processing function
    process_scheduler_messages(messages)

    return jsonify({"message": "Processing completed successfully"}), 200


CLIENT_ID = os.getenv('EMAIL_ASSISTANT_CLIENT_ID')
CLIENT_SECRET = os.getenv('EMAIL_ASSISTANT_CLIENT_SECRET')
REDIRECT_URIS = ['http://localhost:8080/callback','http://localhost:8080']
AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'
SCOPE = ['https://mail.google.com/', 'https://www.googleapis.com/auth/calendar']

@app.route('/login')
def login():
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": AUTH_URI,
                "token_uri": TOKEN_URI,
                "redirect_uris": REDIRECT_URIS,
            }
        }, scopes=SCOPE
    )
    flow.redirect_uri = REDIRECT_URIS[0]
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt="consent"
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    from db.utils import (
        save_token_to_firestore
    )
    state = session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": AUTH_URI,
                "token_uri": TOKEN_URI,
                "redirect_uris": REDIRECT_URIS,
            }
        }, scopes=SCOPE, state=state
    )
    flow.redirect_uri = REDIRECT_URIS[0]
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    print("credentials", credentials.refresh_token)
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    user_id = "dev_123"  # Determine the user ID somehow, e.g., from the session or user email
    token_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    print(token_data)
    save_token_to_db(user_id, token_data)
    save_token_to_firestore(
        user_id=user_id,
        token_data=token_data
    )

    return redirect('http://localhost:3000/api/callback?status=success')

@app.route('/profile')
def profile():
    if 'credentials' not in session:
        return 'You are not logged in! <a href="/login">Login</a>'
    
    credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    gmail = googleapiclient.discovery.build('gmail', 'v1', credentials=credentials)
    results = gmail.users().messages().list(userId='me', maxResults=10).execute()
    return str(results)

@app.route('/')
def index():
    return 'Welcome! <a href="/login">Login with Google</a>'

if __name__ == '__main__':
    app.run(port=8080, debug=True)
