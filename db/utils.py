import json
TOKEN_DB_PATH = 'token_db.json'

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