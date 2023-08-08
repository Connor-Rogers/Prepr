"""
firebase.py

This module provides an interface for connecting and interacting with Firebase.
It initializes Firebase Admin with a given credentials file, allows access to Firestore, 
and provides a client for Google Cloud Storage.

Dependencies:
    - firebase_admin: A library for integrating Firebase Admin SDK.
    - google.cloud: Google Cloud client libraries.

Usage:
    Import the necessary components from this module to work with Firestore and 
    Google Cloud Storage in your application.
"""
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import storage
import json

cred = credentials.Certificate("prepr_fb_secret.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
buckit = storage.Client.from_service_account_json("prepr_fb_secret.json")
