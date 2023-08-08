# Prepr API
## Flask API with Firebase Authentication

This API provides a simple and secure way to create Flask endpoints protected by Firebase Authentication. With this system, each request to the protected endpoints must be accompanied by a valid Firebase ID token.

## Features

** Firebase Authentication: ** Protect your Flask endpoints with Firebase authentication.
User Information: Once authenticated, access user details in your route using Flask's global g object.

## Prerequisites

Python 3.x
A Firebase project setup and necessary credentials.
Setup

### Clone the Repository
```git clone https://github.com/connor-rogers/Prepr.git ```
``` cd flask-firebase-api ```
### Set Up a Virtual Environment (recommended)
```python -m venv venv```
```source venv/bin/activate```
### Install Dependencies
``` pip install -r requirements.txt ```
### Setup Firebase Credentials
Before running the application, ensure you have set up your Firebase credentials. Place the service account key JSON file obtained from the Firebase console in the project directory and set an environment variable pointing to it:
``` export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/serviceAccountKey.json" ```
### Run the Flask API
```flask run```
This will start your Flask API on http://127.0.0.1:5000/.
## Usage
To access a protected endpoint, ensure you send the Firebase ID token in the Authorization header of your request:
```Authorization: Bearer YOUR_FIREBASE_ID_TOKEN```

## Error Handling

If a request lacks a token or provides an invalid one, the API will return a respective error message and HTTP status code.

## Contributing

Feel free to contribute to this project by submitting a PR. Ensure that you include tests and documentation for any added features.

## License

This project is licensed under the GPL 3.0 License.

