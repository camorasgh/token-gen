import json

class Config:
    def __init__(self):
        self.config_file = 'tempmail_config.json'

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