from bs4 import BeautifulSoup
import requests
import re
import tweepy
from urllib.parse import unquote
import os
# Your Twitter API credentials

# Your Twitter API credentials
API_KEY = os.getenv("API_KEY")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")



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

def gather_contact_info(email, name, website=None):
    """Gather relevant information about a contact."""
    domain = email.split('@')[-1]
    twitter_data = search_social_profile(name, 'Twitter')
    linkedin_data = search_social_profile(name, 'LinkedIn')
    if not website:
        website_guess = f"https://www.{domain}"
        try:
            response = requests.get(website_guess)
            if response.status_code == 200:
                website = website_guess
        except:
            website = None  # In case of any exception, website remains None

    return {
        "name": name,
        "email": email,
        "website": website,
        "twitter_profile": twitter_data.get("profile_url"),
        "twitter_image": twitter_data.get("profile_image"),
        "linkedin_profile": linkedin_data.get("profile_url"),
        "linkedin_image": linkedin_data.get("profile_image")
    }

# Example usage:
info = gather_contact_info("elon.musk@spacex.com", "chris dixon")
print(info)
