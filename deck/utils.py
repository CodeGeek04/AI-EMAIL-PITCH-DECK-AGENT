from bs4 import BeautifulSoup
import requests
import re
import tweepy
from urllib.parse import unquote
import os

import pprint
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import AsyncChromiumLoader
from langchain.document_transformers import BeautifulSoupTransformer
from langchain.chains import create_extraction_chain
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage


schema = {
    "properties": {
        "firm_about": {"type": "string"},
        "firm_investments": {"type": "string"},
    },
    "required": ["news_article_title", "news_article_summary"],
}

def extract(content: str, schema: dict):
    return create_extraction_chain(schema=schema, llm=llm).run(content)



# Your Twitter API credentials

# Your Twitter API credentials
API_KEY = os.getenv("TWITTER_API_KEY_V2")
API_SECRET_KEY = os.getenv("TWITTER_API_SECRET_KEY_V2")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN_V2")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET_V2")



# Set up the tweepy authorization
auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# Create a tweepy API object
api = tweepy.API(auth)

def search_web(query):
    search_url = f"https://www.google.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

# def get_recent_tweets(twitter_username):
#   # Authenticate with Twitter API
#   auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
#   auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
  
#   api = tweepy.API(auth)

#   # Fetch most recent tweets
#   tweets = api.user_timeline(screen_name=twitter_username, count=10)

#   # Extract text from tweets
#   recent_tweets = [tweet.text for tweet in tweets]
  
#   return recent_tweets
def get_recent_tweets(twitter_username):

  # Authenticate with Twitter API
  auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
  auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

  api = tweepy.API(auth)
  user = api.search_users(twitter_username)
  print(user)
#   user_id = 
  # Fetch most recent tweets  
  tweets = api.user_timeline(screen_name=twitter_username, count=10)

  # Extract text from tweets
  recent_tweets = [tweet.text for tweet in tweets]
  
  return recent_tweets

def get_direct_twitter_profile_url(name):
    """Search for the Twitter profile and extract the direct URL."""
    soup = search_web(name + " Twitter profile")
    for a in soup.find_all('a', href=True):
        url = a['href']
        if ('twitter.com' in url or 'x.com' in url) and not 'status' in url:
            # Extracting the actual Twitter URL from the Google redirect URL
            match = re.search(r'url=(https://twitter\.com/[^&]+)', url)
            if match:
                return match.group(1)
    return None

def get_twitter_profile_image(username):
    print("fetching username, ", username)
 
    """Get the profile image using the Twitter API."""
    try:
        user = api.get_user(screen_name=username)
        return user.profile_image_url_https
    except Exception as e:
        print(f"Error fetching profile image for {username}:", e)
        return None

def search_twitter_profile(name):
    """Find the Twitter profile URL of a person and scrape for profile image."""
    profile_url = get_direct_twitter_profile_url(name)
    if profile_url:
        # Decode the URL
        decoded_url = unquote(profile_url)
        
        # Extract the username
        username = decoded_url.split("twitter.com/")[-1].split("?")[0]
        
        profile_image = get_twitter_profile_image(username)
        return {
            "profile_url": profile_url,
            "profile_image": profile_image
        }
    return None

def search_social_profile(name, platform):
    """Retrieve the social media profile and profile image URLs."""
    profile_url = None
    profile_image = None
    if platform == "Twitter":
        twitter_data = search_twitter_profile(name)
        if twitter_data:
            profile_url = twitter_data.get("profile_url")
            profile_image = twitter_data.get("profile_image")
    elif platform == "LinkedIn":
        soup = search_web(name + f" {platform} profile")
        image_tag = soup.find("img", {"class": "ivg-i"})
        if image_tag:
            profile_image = image_tag["src"]
    return {
        "profile_url": profile_url,
        "profile_image": profile_image
    }

def summarize_website(extracted_content):
    from langchain.chat_models import ChatOpenAI
    from langchain.chains.summarize import load_summarize_chain
    from langchain.document_loaders import TextLoader
    from langchain.text_splitter import CharacterTextSplitter
    from langchain.docstore.document import Document

    text_splitter = CharacterTextSplitter()
    texts = text_splitter.split_text(extracted_content)
    # Create multiple documents
    docs = [Document(page_content=t) for t in texts]
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    # Text summarization
    chain = load_summarize_chain(llm, chain_type='map_reduce')

    summary = chain.run(docs)
    print(summary)
    return summary

def scrape_website_for_info(website_url):
    print("scraping for ", website_url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    
    # Start with the main page
    response = requests.get(website_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract main page content
    main_page_content = " ".join([p.text for p in soup.find_all('p')])
    
    # Identify potential links to crawl
    potential_links = [a['href'] for a in soup.find_all('a', href=True) if 'about' in a['href'].lower() or 'mission' in a['href'].lower() or 'portfolio' in a['href'].lower() or 'investments' in a['href'].lower()]
    print("main_page_content", main_page_content)
    # Extract content from these links
    additional_content = ""
    for link in potential_links:
        # Construct full URL if relative path is given
        full_url = link if "http" in link else website_url + link
        response = requests.get(full_url, headers=headers)
        link_soup = BeautifulSoup(response.content, 'html.parser')
        additional_content += " ".join([p.text for p in link_soup.find_all('p')])
    
    # Combine and return
    return main_page_content + " " + additional_content


def gather_contact_info(email, name, website=None):
    domain = email.split('@')[-1]
    twitter_data = search_social_profile(name, 'Twitter')
    linkedin_data = search_social_profile(name, 'LinkedIn')
    print('twitter_data', twitter_data)
    # Scrape website info if website exists
    entity_info = None
    if not website:
        website = f"https://www.{domain}"
    
    # Now, we try to scrape the website (either guessed or provided)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.3",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(website, headers=headers)
        print(response)
        if response.status_code == 200:
            website_info = scrape_website_for_info(website)
            entity_info = summarize_website(website_info)
        else:
            website = None  # If the status code is not 200, set website to None
    except Exception as e:
        print(f'Error fetching website {website}:', e)
        website = None

    print("TWItter", twitter_data)
   
    
    return_data =  {
        "name": name,
        "email": email,
        "website": website,
        "entity_info": entity_info,   # Add this line
        "twitter_profile": twitter_data.get("profile_url"),
        "twitter_image": twitter_data.get("profile_image"),
        "linkedin_profile": linkedin_data.get("profile_url"),
        "linkedin_image": linkedin_data.get("profile_image")
    } 
    # if twitter_data.get('profile_url'):
    #     username = twitter_data['profile_url'].split('/')[-1]
    #     recent_tweets = get_recent_tweets(username)
    # return_data["recent_tweets"] = recent_tweets
    return return_data
# Example usage:
# info = gather_contact_info("elon.musk@spacex.com", "chris dixon")
# print(info)
from googleapiclient.discovery import build
import base64
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
import email
# Initialize the Gmail API client
def update_email_draft(creds, draft_id, file_path, file_name):
    """Update an existing draft with an attachment."""
    
    # Initialize the Gmail API client
    gmail_service = build('gmail', 'v1', credentials=creds)

    # Step 1: Retrieve the Existing Draft
    existing_draft = gmail_service.users().drafts().get(userId="me", id=draft_id).execute()
    raw_existing_message = existing_draft['message']['raw']
    decoded_message = base64.urlsafe_b64decode(raw_existing_message.encode('ASCII'))

    # Step 2: Modify the MIME Message
    mime_message = email.message_from_bytes(decoded_message)
    
    # Load the file data
    with open(file_path, "rb") as f:
        file_data = f.read()
    
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(file_data)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment', filename=file_name)
    mime_message.attach(attachment)
    
    raw_modified_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("utf-8")

    # Step 3: Update the Draft
    updated_draft = {
        'id': draft_id,
        'message': {
            'raw': raw_modified_message
        }
    }
    result = gmail_service.users().drafts().update(userId="me", id=draft_id, body=updated_draft).execute()
    
    return result
