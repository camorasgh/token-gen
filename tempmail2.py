import requests
import json
import re
import time
import uuid
import random
import subprocess
import sys
from datetime import datetime, timedelta

from html2text import HTML2Text

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TempMailDiscordVerifier:
    def __init__(self, api_key=None):
        self.base_url = 'https://api.tempmail.lol'
        self.config_file = 'tempmail_config.json'
        self.api_key = api_key or self.load_api_key()
        self.html_converter = HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True

    def load_api_key(self) -> str:
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config.get('api_key')
        except FileNotFoundError:
            api_key = input("Enter TempMail API Key: ")
            self.save_api_key(api_key)
            return api_key

    def save_api_key(self, api_key) -> None:
        with open(self.config_file, 'w') as f:
            json.dump({'api_key': api_key}, f)

    def generate_random_username(self):
        adjectives = ['Cool', 'Epic', 'Awesome', 'Brave', 'Swift', 'Silent', 'Mystic', 'Rapid', 'Clever', 'Bold']
        nouns = ['Gamer', 'Wolf', 'Phoenix', 'Dragon', 'Ninja', 'Warrior', 'Knight', 'Eagle', 'Shadow', 'Titan']
        numbers = ''.join([str(random.randint(0, 9)) for _ in range(3)])
        return f"{random.choice(adjectives)}{random.choice(nouns)}{numbers}"

    def generate_random_password(self, length=12):
        characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+'
        return ''.join(random.choice(characters) for _ in range(length))

    def generate_random_birthdate(self):
        current_year = datetime.now().year
        birth_year = random.randint(1980, current_year - 18)
        birth_month = random.randint(1, 12)
        
        if birth_month in [1, 3, 5, 7, 8, 10, 12]:
            birth_day = random.randint(1, 31)
        elif birth_month in [4, 6, 9, 11]:
            birth_day = random.randint(1, 30)
        else:  # February
            birth_day = random.randint(1, 28)
        
        return birth_year, birth_month, birth_day

    def fill_discord_registration(self, driver, email, display_name, username, password, birth_year, birth_month, birth_day):
        wait = WebDriverWait(driver, 20)

        try:
            email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="email"]')))
            email_input.clear()
            email_input.send_keys(email)

            display_name_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="displayName"]')))
            display_name_input.clear()
            display_name_input.send_keys(display_name)

            username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="username"]')))
            username_input.clear()
            username_input.send_keys(username)

            password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]')))
            password_input.clear()
            password_input.send_keys(password)

            year_select = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="year"]')))
            year_select.clear()
            year_select.send_keys(str(birth_year))

            month_select = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="month"]')))
            month_select.clear()
            month_select.send_keys(str(birth_month))

            day_select = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="day"]')))
            day_select.clear()
            day_select.send_keys(str(birth_day))

            continue_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Continue")]')))
            continue_button.click()

        except Exception as e:
            print(f"Error filling registration form: {e}")
            driver.save_screenshot('registration_error.png')
            raise

    def create_inbox(self) -> dict | None:
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

    def fetch_emails(self, token) -> dict | None:
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

    def extract_verification_link(self, emails) -> str | None:
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

    def run(self) -> str | None:
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

        username = self.generate_random_username()
        display_name = username
        password = self.generate_random_password()
        birth_year, birth_month, birth_day = self.generate_random_birthdate()

        print(f"🔒〡Username: {username}")
        print(f"🔑〡Password: {password}")
        print(f"🎂〡Birth Date: {birth_month}/{birth_day}/{birth_year}")

        chrome_options = Options()
        chrome_options.add_argument('--incognito')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('https://discord.com/register')

        try:
            self.fill_discord_registration(
                driver, 
                email, 
                display_name, 
                username, 
                password, 
                birth_year, 
                birth_month, 
                birth_day
            )

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
                            driver.get(verification_link)

                        return verification_link

                time.sleep(10)
                try_count += 1
                print(f"🕵️〡Checking emails... (Attempt {try_count}/{max_tries}) {time.strftime('%H:%M:%S')}")

            print("❌〡No verification link found after multiple attempts.")
            return None

        except Exception as e:
            print(f"Error during registration: {e}")
            driver.save_screenshot('registration_error.png')
        finally:
            driver.quit()

def main():
    verifier = TempMailDiscordVerifier()
    verifier.run()

if __name__ == '__main__':
    main()
