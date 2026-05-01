import json

def load_test_data():
    with open("data/test_data.json") as f:
        return json.load(f)
    
def load_employee_data():
    with open("test_data/new_emp_details.json") as f:
        return json.load(f)