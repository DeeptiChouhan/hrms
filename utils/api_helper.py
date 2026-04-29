import requests
from utils.config import API_URL

def login_api(email, password):
    headers = {
        "x-tenant-domain": "https://hrms.eznity.ai"
    }

    data = {
        "email": email,
        "password": password
    }

    response = requests.post(f"{API_URL}/login", json=data, headers=headers)
    return response