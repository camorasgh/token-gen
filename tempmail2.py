import requests
import json
import re
import time
import webbrowser
import uuid

from html2text import HTML2Text


class TempMailDiscordVerifier:
    def __init__(self, api_key=None):
        self.base_url = 'https://api.tempmail.lol'
        self.config_file = 'tempmail_config.json'
        self.api_key = api_key or self.load_api_key()
        self.html_converter = HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True

    def load_api_key(self) -> str:
        """
        Load the API key from a configuration file or prompt the user to enter it.

        This method attempts to read the API key from a JSON configuration file.
        If the file is not found, it prompts the user to enter the API key and
        saves it for future use.

        Returns:
            str: The API key for TempMail service.

        Raises:
            FileNotFoundError: If the configuration file is not found (handled internally).
        """
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

    def create_inbox(self) -> dict | None:
        """
        Create a new temporary email inbox using the TempMail API.

        This method attempts to create an inbox using different payload options,
        including an empty payload, a payload with a random prefix, a payload with
        a specific domain, and a payload with both a random prefix and specific domain.

        Returns:
            dict or None: A dictionary containing the created inbox details if successful,
                          including the email address and token. Returns None if all
                          creation attempts fail.

        Raises:
            requests.exceptions.RequestException: If there's an error in making the API request.

        Note:
            The method will try different payload options in case of failure,
            printing error messages for each failed attempt.
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


    def fetch_emails(self, token) -> dict | None:
        """
        Fetch emails from the temporary email inbox using the TempMail API.

        This method sends a GET request to the TempMail API to retrieve emails
        associated with the given token.

        Args:
            token (str): The unique token associated with the temporary email inbox.

        Returns:
            dict or None: A dictionary containing the fetched emails if the request is
                          successful (status code 200). Returns None if there's an error
                          or if the request fails.

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


    def extract_verification_link(self, emails) -> str | None:
        """
        Extract the Discord verification link from a list of emails.

        This function searches through the provided emails for a Discord verification
        email and attempts to extract the verification link from its content.

        Args:
            emails (list): A list of dictionaries, where each dictionary represents
                           an email with 'subject' and 'body' keys.

        Returns:
            str or None: The extracted Discord verification link if found, otherwise None.

        Note:
            The function first checks for HTML content in the email body and converts
            it to plain text if present. It then uses a regular expression to search
            for the Discord verification link pattern.
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


    def run(self) -> str | None:
        """
        Execute the main workflow for creating a temporary email and retrieving a Discord verification link.

        This method performs the following steps:
        1. Creates a temporary email inbox.
        2. Waits for incoming emails and checks for a Discord verification link.
        3. If found, saves the link to a file and optionally opens it in a browser.

        Returns:
            str or None: The Discord verification link if found, otherwise None.

        Note:
            - The method will make multiple attempts to fetch emails and extract the verification link.
            - It will print status updates and prompts to the console during execution.
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