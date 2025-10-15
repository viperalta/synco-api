 # convert_token_pickle_to_json.py
import pickle, json
from google.oauth2.credentials import Credentials

with open("token.json", "rb") as f:
    creds = pickle.load(f)

# Produce JSON serializable por Google (incluye refresh_token si existe)
token_json = creds.to_json()
print(token_json)