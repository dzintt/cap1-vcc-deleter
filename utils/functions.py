import json

def get_cookies():
    with open("cookies.json", "r") as file:
        return json.load(file)