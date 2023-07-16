import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import storage
import json

cred = credentials.Certificate("prepr_fb_secret.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
buckit = storage.Client.from_service_account_json("prepr_fb_secret.json")

## Aggregation Functions
