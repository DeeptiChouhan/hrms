import json

def load_test_data():
    with open("data/test_data.json") as f:
        return json.load(f)