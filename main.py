import requests
import re
import time
import uuid

from core.config import Config
from core.generate import Userdata

from datetime import datetime
from html2text import HTML2Text
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Verifier:
    def __init__(self, api_key=None):
        self.base_url = 'https://api.tempmail.lol'
        self.config_file = 'tempmail_config.json'
        self.api_key = api_key or Config.load_api_key()
        self.html_converter = HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True

    def fill_discord_registration(self, driver, email: str, display_name: str, username: str, password: str, birth_year: int, birth_month: int, birth_day: int) -> None:
        """
        Fills out the Discord registration form using Selenium WebDriver.

        This function automates the process of filling out the Discord registration form
        by locating form elements and inputting the provided user information.

        Args:
            driver (WebDriver): The Selenium WebDriver instance.
            email (str): The email address to be used for registration.
            display_name (str): The display name for the Discord account.
            username (str): The username for the Discord account.
            password (str): The password for the Discord account.
            birth_year (int): The birth year for the account.
            birth_month (int): The birth month for the account.
            birth_day (int): The birth day for the account.

        Raises:
            Exception: If there's an error during the form filling process.

        Returns:
            Currently None

        Note:
            This function uses explicit waits to ensure elements are present before interacting with them.
            If an error occurs, it saves a screenshot of the page for debugging purposes.
        """
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
            driver.save_screenshot('registration_error_unknown.png')
            raise

    def create_inbox(self) -> dict | None:
        """
        Creates a new temporary email inbox using the TempMail API.

        This function attempts to create an inbox using different payload options,
        including an empty payload, a payload with a random prefix, a payload with
        a specific domain, and a payload with both a random prefix and specific domain.

        Returns:
            dict | None: A dictionary containing the created inbox details if successful,
                         including the email address and token. Returns None if all
                         creation attempts fail.

        Raises:
            requests.exceptions.RequestException: If there's an error in making the API request.

        Note:
            The function will try different payload options in case of failure,
            and will print error messages for failed attempts.
        """
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


    def fetch_emails(self, token: str) -> dict | None:
        """
        Fetches emails from the temporary email inbox using the TempMail API.

        This function sends a GET request to the TempMail API to retrieve emails
        associated with the given token.

        Args:
            token (str): The unique token associated with the temporary email inbox.

        Returns:
            dict | None: A dictionary containing the email data if the request is successful,
                         or None if there's an error or no emails are found.

        Raises:
            requests.exceptions.RequestException: If there's an error in making the API request.
        """
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


    def extract_verification_link(self, emails: list) -> str | None:
        """
        Extracts the Discord verification link from a list of emails.

        This function searches through the provided emails for a Discord verification email
        and extracts the verification link from it. It first checks for HTML content,
        converts it to plain text if found, and then searches for the verification link
        using a regular expression pattern.

        Args:
            emails (list): A list of email dictionaries, each containing 'subject' and 'body' keys.

        Returns:
            str | None: The extracted Discord verification link if found, or None if no link is found.

        """
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


    def create_and_verify_discord_account(self) -> str | None:
        """
        Starts the Discord account creation and verification process.

        This method performs the following steps:
        1. Creates a temporary email inbox
        2. Generates random user data (username, password, birthdate)
        3. Fills out the Discord registration form using Selenium
        4. Waits for and extracts the verification link from the received email
        5. Optionally opens the verification link in the browser

        Returns:
            str | None: The Discord verification link if found, None otherwise.

        Raises:
            Exception: If an error occurs during the registration process.

        Note:
            - The method uses Selenium WebDriver to interact with the Discord registration page.
            - It attempts to fetch the verification email multiple times with a delay between attempts.
            - The verification link is saved to a file named 'discord_verification_link.txt'.
        """
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

        username = Userdata.generate_random_username()
        password = Userdata.generate_random_password()
        display_name = username
        birth_year, birth_month, birth_day = Userdata.generate_random_birthdate()

        print(f"📧〡Email: {email}")
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

            max_tries = 20
            try_count = 0
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
            driver.save_screenshot('registration_error_unknown.png')
        finally:
            driver.quit()



if __name__ == '__main__':
    verifier = Verifier()
    verifier.create_and_verify_discord_account()