
# --- Firebase & Telegram Config ---
# IMPORTANT: Replace with your actual Firebase and Telegram details
FIREBASE_SERVICE_ACCOUNT_KEY = 'firebase_service_account.json'
FIREBASE_DATABASE_URL = 'https://schoolfinderabj-default-rtdb.europe-west1.firebasedatabase.app/' 
TELEGRAM_BOT_TOKEN = '7678276226:AAGNAWAFYhWIfJ6BWvld6BDki2fVDFWyb90'
TELEGRAM_CHAT_ID = '1206974757'

# --- Configuration ---
MODEL_PATH = 'best_agrosense_model.h5'
CLASS_INDICES_PATH = 'class_indices.json'
RECOMMENDATIONS_PATH = 'recommendations.json' 
IMG_HEIGHT = 224
IMG_WIDTH = 224

# --- Global Language/Text Mapping ---
# Dictionary for language display names
LANGUAGE_MAP = {
    'en': 'English',
    'ig': 'Igbo',
    'ha': 'Hausa',
    'yo': 'Yoruba',
    'fr': 'French',
    'es': 'Spanish',
    'sw': 'Swahili',
    'de': 'German',
    # Add more as needed
}

# Dictionary for multilingual UI text 
UI_TEXT_MAP = {
    'Overview': { 'en': 'Overview', 'ig': 'Nleleanya' },
    'Treatment': { 'en': 'Treatment', 'ig': 'Ọgwụgwọ' },
    'Prevention': { 'en': 'Prevention', 'ig': 'Mgbochi' },
}
