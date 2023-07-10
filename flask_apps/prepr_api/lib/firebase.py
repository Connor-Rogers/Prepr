import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("prepr_fb_secret.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


## Aggregation Functions
