import requests
import json
import os
import re
import time
import webbrowser
import uuid
import html2text
import urllib.parse

class TempMailDiscordVerifier:
    def __init__(self, api_key=None):
        self.base_url = 'https://api.tempmail.lol'
        self.config_file = 'tempmail_config.json'
        self.api_key = api_key or self.load_api_key()
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True

    def load_api_key(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config.get('api_key')
        except FileNotFoundError:
            api_key = input("Enter TempMail API Key: ")
            self.save_api_key(api_key)
            return api_key

    def save_api_key(self, api_key):
        with open(self.config_file, 'w') as f:
            json.dump({'api_key': api_key}, f)

    def create_inbox(self):
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }
        
        payload_options = [
            {},
            {'prefix': str(uuid.uuid4())[:8]},
            {'domain': 'tempmail.lol'},
            {'prefix': str(uuid.uuid4())[:8], 'domain': 'tempmail.lol'}
        ]

        for payload in payload_options:
            try:
                response = requests.post(
                    f'{self.base_url}/v2/inbox/create', 
                    headers=headers,
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    return response.json()
                
                print(f"Attempt failed: {response.status_code} - {response.text}")
            
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")

        return None

    def fetch_emails(self, token):
        headers = {
            'Authorization': self.api_key,
            'User-Agent': 'Mozilla/5.0'
        }
        
        try:
            response = requests.get(
                f'{self.base_url}/v2/inbox', 
                params={'token': token},
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None

    def extract_verification_link(self, emails):
        for email in emails:
            if 'Discord' in email.get('subject', ''):
                if 'html' in email.get('body', '').lower():
                    plain_text = self.html_converter.handle(email['body'])
                    
                    link_pattern = r'https://click\.discord\.com/ls/click\?[^\s]+'
                    match = re.search(link_pattern, plain_text, re.IGNORECASE)
                    
                    if match:
                        return match.group(0)

                link_pattern = r'https://click\.discord\.com/ls/click\?[^\s]+'
                match = re.search(link_pattern, email.get('body', ''), re.IGNORECASE)
                
                if match:
                    return match.group(0)

        return None

    def run(self):
        print("🚀〡Creating Temporary Email...")
        inbox = self.create_inbox()
        
        if not inbox:
            print("❌〡Failed to create inbox. Possible solutions:")
            print("1. Check your API key")
            print("2. Verify network connection")
            print("3. Check API status")
            return

        email = inbox['address']
        token = inbox['token']

        print(f"📧〡Email: {email}")
        print("⏳〡Waiting for Discord verification link...")

        try_count = 0
        max_tries = 20

        while try_count < max_tries:
            emails_data = self.fetch_emails(token)
            
            if emails_data and emails_data.get('emails'):
                verification_link = self.extract_verification_link(emails_data['emails'])
                
                if verification_link:
                    print("\n🎉〡Discord Verification Link Found!")
                    print(f"🔗〡Link: {verification_link}")
                    
                    with open('discord_verification_link.txt', 'w') as f:
                        f.write(verification_link)
                    
                    choice = input("Open verification link in browser? (y/n): ").lower()
                    if choice == 'y':
                        webbrowser.open(verification_link)
                    
                    return verification_link

            time.sleep(10)
            try_count += 1
            print(f"🕵️〡Checking emails... (Attempt {try_count}/{max_tries}) {time.strftime('%H:%M:%S')}")

        print("❌〡No verification link found after multiple attempts.")
        return None

def main():
    verifier = TempMailDiscordVerifier()
    verifier.run()

if __name__ == '__main__':
    main()