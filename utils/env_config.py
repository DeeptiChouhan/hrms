import os
from dotenv import load_dotenv
from utils.data_reader import load_config

load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def get_headless_value():
    config = load_config()

    headless_env = os.getenv("HEADLESS")

    if headless_env is not None:
        return headless_env.lower() == "true"

    return config["headless"]