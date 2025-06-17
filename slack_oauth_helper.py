#!/usr/bin/env python3
"""
Slack OAuth Helper
Helps generate the OAuth URL and exchange code for token.
"""

import os
import requests
from urllib.parse import urlencode

# Your app credentials
CLIENT_ID = "8991856883520.9064120674466"
CLIENT_SECRET = "ff7a3eeef8aeb4502c9ba1696f06f21a"
REDIRECT_URI = "http://localhost:5000/slack/oauth/callback"

def generate_oauth_url():
    """Generate Slack OAuth URL for installation."""
    
    params = {
        'client_id': CLIENT_ID,
        'scope': 'chat:write,channels:read,groups:read',
        'redirect_uri': REDIRECT_URI,
        'state': 'storage-monitoring-app'
    }
    
    oauth_url = f"https://slack.com/oauth/v2/authorize?{urlencode(params)}"
    return oauth_url

def exchange_code_for_token(code):
    """Exchange OAuth code for access token."""
    
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    
    response = requests.post('https://slack.com/api/oauth.v2.access', data=data)
    return response.json()

if __name__ == '__main__':
    print("Slack OAuth Helper")
    print("=" * 50)
    print("\n1. Visit this URL to install the app to your workspace:")
    print(f"\n{generate_oauth_url()}\n")
    print("2. After authorization, you'll get a code parameter in the redirect URL")
    print("3. Use that code to get your Bot Token")
    print("\nAlternatively, you can:")
    print("- Go directly to https://api.slack.com/apps/A091W3JKUDQ/oauth")
    print("- Add scopes: chat:write, channels:read")
    print("- Click 'Install to Workspace'")
    print("- Copy the 'Bot User OAuth Token' (starts with xoxb-)")