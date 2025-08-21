#!/usr/bin/env python3
"""
GitHub Codespaces Viewer - Simple script to view your GitHub Codespaces
Usage: python codespaces_viewer.py
Set GITHUB_TOKEN environment variable with a personal access token
"""

import os
import sys
import requests
from datetime import datetime

def get_github_token():
    """Get GitHub token from environment or prompt user"""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("GitHub token not found in GITHUB_TOKEN environment variable.")
        print("You can create a token at: https://github.com/settings/tokens")
        print("Make sure to include 'codespace' permissions.")
        token = input("Enter your GitHub token: ").strip()
    return token

def format_date(date_str):
    """Format ISO date string to readable format"""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return date_str

def list_codespaces(token):
    """List all codespaces for the authenticated user"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.get('https://api.github.com/user/codespaces', headers=headers)
        
        if response.status_code == 401:
            print("❌ Authentication failed. Please check your GitHub token.")
            return False
        elif response.status_code != 200:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        codespaces = data.get('codespaces', [])
        
        if not codespaces:
            print("📦 No codespaces found for your account.")
            return True
        
        print(f"🚀 Found {len(codespaces)} codespace(s):\n")
        
        for i, cs in enumerate(codespaces, 1):
            print(f"{i}. {cs['display_name'] or cs['name']}")
            print(f"   📁 Repository: {cs['repository']['full_name']}")
            print(f"   🔄 State: {cs['state']}")
            print(f"   💻 Machine: {cs['machine']['display_name']}")
            print(f"   📅 Created: {format_date(cs['created_at'])}")
            if cs.get('last_used_at'):
                print(f"   🕒 Last used: {format_date(cs['last_used_at'])}")
            if cs.get('web_url'):
                print(f"   🌐 URL: {cs['web_url']}")
            print()
        
        return True
        
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        return False

def get_user_info(token):
    """Get information about the authenticated user"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.get('https://api.github.com/user', headers=headers)
        
        if response.status_code == 200:
            user = response.json()
            print(f"👤 Authenticated as: {user['login']}")
            if user.get('name'):
                print(f"   Name: {user['name']}")
            print()
            return True
        else:
            print(f"❌ Error getting user info: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        return False

def main():
    """Main function"""
    print("🌌 GitHub Codespaces Viewer")
    print("=" * 40)
    
    token = get_github_token()
    if not token:
        sys.exit(1)
    
    # Get user info first
    if not get_user_info(token):
        sys.exit(1)
    
    # List codespaces
    if not list_codespaces(token):
        sys.exit(1)
    
    print("✅ Done!")

if __name__ == "__main__":
    main()