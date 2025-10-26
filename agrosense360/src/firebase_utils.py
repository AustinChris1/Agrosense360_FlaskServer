
import firebase_admin
from firebase_admin import credentials, db
from .config import FIREBASE_SERVICE_ACCOUNT_KEY, FIREBASE_DATABASE_URL

def initialize_firebase():
    try:
        # Check if Firebase has already been initialized (Gunicorn might load the app multiple times)
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_KEY)
            firebase_admin.initialize_app(cred, {
                'databaseURL': FIREBASE_DATABASE_URL
            })
            print("Firebase Admin SDK initialized successfully.")
        else:
            print("Firebase Admin SDK already initialized.")
    except Exception as e:
        # Be less aggressive on exit, just log the error and continue if possible.
        print(f"Error initializing Firebase Admin SDK: {e}. Data logging may be unavailable.")
        # We don't exit here, as the main app functionality should still work.

def push_prediction_to_firebase(data):
    try:
        # Ensure the app is initialized before calling db.reference
        if firebase_admin._apps:
            ref = db.reference('/predictions')
            ref.push(data)
            print("Data pushed to Firebase successfully.")
        else:
            print("WARNING: Firebase not initialized. Skipping database logging.")
    except Exception as e:
        print(f"Error pushing to Firebase: {e}")
