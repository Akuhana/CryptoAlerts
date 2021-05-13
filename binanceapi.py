import os, time
import json

class BinanceAPI:
    api_key     = None
    secret_key  = None
    
    def __init__(self):
        self.load_api_keys()
    
    def load_api_keys(self):
        config_dir = os.path.join(os.getenv("LOCALAPPDATA"), "CryptoAlerts/config.json")
        
        while not os.path.exists(config_dir):
            print("Loading api keys...")
            time.sleep(2)
            
        try:
            with open(config_dir) as f:
                data            = json.load(f)
                self.api_key    = data["api_key"]
                self.api_secret = data["api_secret"]
        except FileNotFoundError as e:
            print(f"There is no such file: {config_dir}")
        
        print("Api keys were loaded successfully.")