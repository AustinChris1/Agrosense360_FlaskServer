import os
import numpy as np
from flask import Flask, request, jsonify, render_template_string
from tensorflow.keras.models import load_model
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from PIL import Image, ImageStat 
import cv2 
import requests 
from flask_cors import CORS 
import json
import firebase_admin
from firebase_admin import credentials, db
from googletrans import Translator 
from io import BytesIO 
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app) 
load_dotenv()
# --- Firebase & Telegram Config ---
FIREBASE_KEY_ENV_VAR = 'FIREBASE_KEY_JSON'
# --- CORRECT: Read variables from the environment (loaded by load_dotenv()) ---
FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

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
    'Overview': {'en': 'Overview', 'ig': 'Nleleanya' },
    'Treatment': {'en': 'Treatment', 'ig': 'Ọgwụgwọ' },
    'Prevention': {'en': 'Prevention', 'ig': 'Mgbochi' },
}

# Global variables to store the loaded model and class names
model = None
class_names = None
recommendations_db = None
translator = Translator()

# --- Custom Keras Objects (Crucial for loading your model) ---
class F1Score(tf.keras.metrics.Metric):
    def __init__(self, name="f1_score", **kwargs):
        super(F1Score, self).__init__(name=name, **kwargs)
        self.precision = tf.keras.metrics.Precision()
        self.recall = tf.keras.metrics.Recall()

    def update_state(self, y_true, y_pred, sample_weight=None):
        self.precision.update_state(y_true, y_pred, sample_weight)
        self.recall.update_state(y_true, y_pred, sample_weight)

    def result(self):
        precision = self.precision.result()
        recall = self.recall.result()
        return 2 * (precision * recall) / (precision + recall + tf.keras.backend.epsilon())

    def reset_state(self):
        self.precision.reset_state()
        self.recall.reset_state()

class FixedDropout(tf.keras.layers.Dropout):
    def call(self, inputs, training=None):
        return super().call(inputs, training=True)

# --- Load Model, Class Names, and Recommendations on startup ---
def load_resources():
    global model, class_names, recommendations_db
    print("Loading model and resources...")
    
    # Initialize Firebase Admin SDK
    try:
        # 1. Check if Firebase is already initialized
        if not firebase_admin._apps:
            
            # --- CORRECT: Get the JSON string from the environment variable ---
            firebase_key_json_str = os.environ.get(FIREBASE_KEY_ENV_VAR)
            
            if not firebase_key_json_str or not FIREBASE_DATABASE_URL:
                print("WARNING: Firebase credentials or database URL not fully set. Database logging will be skipped.")
                # The function continues to load the model and recommendations
            else:
                try:
                    service_account_info = json.loads(firebase_key_json_str)
                except json.JSONDecodeError as e:
                    print(f"CRITICAL ERROR: Failed to parse Firebase service account JSON: {e}")
                    return

                # Initialize with the dictionary object
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': FIREBASE_DATABASE_URL
                })
                print("Firebase Admin SDK initialized successfully.")
        else:
            print("Firebase Admin SDK already initialized.")
    except Exception as e:
        # The app shouldn't crash if Firebase fails, only skip logging.
        print(f"Error initializing Firebase Admin SDK: {e}. Data logging may be unavailable.")
        
    # 2. Load the Keras Model
    try:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at: {os.path.abspath(MODEL_PATH)}")
            
        model_size_bytes = os.path.getsize(MODEL_PATH)
        print(f"Model file found. Size: {model_size_bytes / (1024*1024):.2f} MB")
        model = load_model(MODEL_PATH, custom_objects={
            'F1Score': F1Score,
            'swish': tf.keras.activations.swish,
            'FixedDropout': FixedDropout
        })
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        # CRITICAL: Stop the server if the ML model isn't available
        raise RuntimeError(f"Failed to load model: {e}")

    # 3. Load Class Names
    try:
        with open(CLASS_INDICES_PATH, 'r') as f:
            loaded_indices = json.load(f)
            class_names = {int(k): v for k, v in loaded_indices.items()}
        print("Class names loaded successfully.")
    except FileNotFoundError:
        raise RuntimeError(f"Error: {CLASS_INDICES_PATH} not found.")

    # 4. Load Recommendations
    try:
        with open(RECOMMENDATIONS_PATH, 'r') as f:
            recommendations_db = json.load(f)
        print("Recommendations loaded successfully.")
    except FileNotFoundError:
        raise RuntimeError(f"Error: {RECOMMENDATIONS_PATH} not found.")

    # --- REMOVED: Redundant and incorrect second Firebase initialization block ---

# --- Translation Function (Enhanced for multilingual text) ---
def get_translated_ui_text(key, lang_code, text_map):
    """Retrieves the UI text translation or falls back to English, adding the English in parenthesis."""
    english_text = text_map[key].get('en', key)
    translated_text = text_map[key].get(lang_code, english_text)

    # If the translated text is different from English, return the format: "Translated (English)"
    if translated_text.lower() != english_text.lower():
        return f"{translated_text} ({english_text})"
    
    # Otherwise, just return the English text
    return english_text

def translate_text(text, dest_language='en'):
    """Translates text to a specified destination language. Handles both single string and list of strings."""
    if dest_language == 'en':
        return text 
        
    try:
        if isinstance(text, list):
            translated_list = []
            for item in text:
                # Use source language 'en' if possible for better results
                translation = translator.translate(item, dest=dest_language, src='en')
                translated_list.append(translation.text)
            return translated_list
        else:
            translation = translator.translate(text, dest=dest_language, src='en')
            return translation.text
            
    except Exception as e:
        print(f"Error during translation to {dest_language}: {e}. Returning original text.")
        return text 

# --- Image Pre-check Functions (Remain the same) ---
def is_low_quality_image(pil_image):
    try:
        img_gray = pil_image.convert("L")
        stat = ImageStat.Stat(img_gray)
        mean_brightness = stat.mean[0]
        stddev = stat.stddev[0]
        return mean_brightness < 20 or stddev < 10
    except Exception as e:
        print(f"Error checking image quality: {e}")
        return True

def is_leaf_detected(pil_image):
    try:
        cv_image = np.array(pil_image)
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        lower_green = np.array([20, 20, 20])
        upper_green = np.array([90, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)
        green_pixel_count = np.sum(mask > 0)
        total_pixels = mask.shape[0] * mask.shape[1]
        green_ratio = green_pixel_count / total_pixels
        return green_ratio > 0.05
    except Exception as e:
        print(f"Error during leaf detection: {e}")
        return False

# --- Telegram Helper Functions ---

def create_telegram_message(predicted_class, confidence, translated_recommendations, lang_code):
    """Formats the prediction and recommendations into a structured Telegram message."""
    
    # Get translated UI strings with English in brackets
    overview_text_ui = get_translated_ui_text('Overview', lang_code, UI_TEXT_MAP)
    treatment_text_ui = get_translated_ui_text('Treatment', lang_code, UI_TEXT_MAP)
    prevention_text_ui = get_translated_ui_text('Prevention', lang_code, UI_TEXT_MAP)

    # Format treatment and prevention lists
    treatment_list = "\n".join([f" • {item}" for item in translated_recommendations['treatment']])
    prevention_list = "\n".join([f" • {item}" for item in translated_recommendations['prevention']])
    
    # Use HTML for formatting in Telegram
    message = f"""
🌱 <b>New Plant Health Scan Alert!</b>
────────────────────
🚨 <b>Disease:</b> <code>{predicted_class}</code>
📊 <b>Confidence:</b> <b>{confidence*100:.2f}%</b>
🌐 <b>Translated to:</b> <i>{LANGUAGE_MAP.get(lang_code, 'N/A')}</i>
────────────────────

📋 <b>{overview_text_ui}</b>
{translated_recommendations['overview']}

💊 <b>{treatment_text_ui}</b> (Action Required)
{treatment_list}

🛡️ <b>{prevention_text_ui}</b> (Long-term Strategy)
{prevention_list}
"""
    return message.strip()

def send_telegram_photo(photo_data, message):
    # --- CORRECTED: Use the global variables which are now read from .env ---
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: 
        print("WARNING: Telegram bot token or chat ID is missing. Skipping Telegram notification.")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    
    # We use 'caption' for the message and set parse_mode to HTML
    data = {
        'chat_id': TELEGRAM_CHAT_ID, 
        'caption': message,
        'parse_mode': 'HTML'
    }
    files = {'photo': photo_data}
    
    try:
        response = requests.post(url, data=data, files=files, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram notification sent.")
            return True
        else:
            print(f"❌ Failed to send Telegram notification. Status: {response.status_code}, Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send Telegram notification due to network error: {e}")
        return False

# --- Main Prediction Endpoint ---
@app.route('/predict', methods=['POST'])
def predict_endpoint():
    if 'file' not in request.files:
        return jsonify({"error": "No image file provided."}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected image file."}), 400
    
    # Get optional language from query parameters, default to English
    dest_lang = request.args.get('lang', 'en').lower()
    
    if file:
        try:
            # Check if model is loaded before proceeding
            if model is None:
                return jsonify({"error": "Model not yet loaded. Server is initializing."}), 503
                
            # 1. Image Pre-processing and Prediction
            pil_img = Image.open(file.stream).convert('RGB')

            if is_low_quality_image(pil_img):
                return jsonify({"error": "Image quality is too low (e.g., too dark, too uniform). Please upload a clearer image."}), 400
            
            if not is_leaf_detected(pil_img):
                return jsonify({"error": "No significant plant leaf detected in the image. Please upload an image of a plant leaf."}), 400

            img_resized = pil_img.resize((IMG_WIDTH, IMG_HEIGHT))
            img_array = image.img_to_array(img_resized)
            img_array = np.expand_dims(img_array, axis=0)
            img_array /= 255.0

            predictions = model.predict(img_array)
            predicted_class_index = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class_index])
            predicted_class_name = class_names.get(predicted_class_index, "Unknown")

            recommendations = recommendations_db.get(predicted_class_name, {
                "overview": "Information not available.",
                "treatment": ["No specific treatment found."],
                "prevention": ["No specific prevention methods found."]
            })

            # Check confidence threshold for "Unknown"
            if confidence < 0.6:
                predicted_class_name = "Unknown"
                recommendations = recommendations_db.get("Unknown", recommendations) 
            
            # 2. Translate Recommendations
            translated_recommendations = {
                "overview": translate_text(recommendations["overview"], dest_lang),
                "treatment": translate_text(recommendations["treatment"], dest_lang),
                "prevention": translate_text(recommendations["prevention"], dest_lang)
            }
            
            # Get the full language name for database logging
            full_language_name = LANGUAGE_MAP.get(dest_lang, dest_lang.upper())
            translated_recommendations['language'] = dest_lang # Log code for dashboard
            translated_recommendations['language_name'] = full_language_name # Log full name

            # 3. Save to Firebase
            firebase_data = {
                "timestamp": tf.timestamp().numpy().tolist(),
                "predicted_class": predicted_class_name,
                "confidence": confidence,
                "recommendations": translated_recommendations # Contains language code and name
            }

            try:
                # Ensure the app is initialized before calling db.reference
                if firebase_admin._apps:
                    ref = db.reference('/predictions')
                    ref.push(firebase_data)
                    print("Data pushed to Firebase successfully.")
                else:
                    print("WARNING: Firebase not initialized. Skipping database logging.")
            except Exception as e:
                print(f"Error pushing to Firebase: {e}")
            
            # 4. Send to Telegram
            img_byte_arr = BytesIO()
            pil_img.save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)
            
            telegram_message = create_telegram_message(
                predicted_class_name, 
                confidence, 
                translated_recommendations,
                dest_lang
            )
            send_telegram_photo(img_byte_arr.getvalue(), message=telegram_message)

            # 5. Return Response
            return jsonify({
                "predicted_class": predicted_class_name,
                "confidence": confidence,
                "recommendations": translated_recommendations
            }), 200

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500
    
    return jsonify({"error": "Something went wrong."}), 500

# --- Health Check Endpoint (remains the same) ---
@app.route('/health', methods=['GET'])
def health_check():
    # This check now relies on the global variables being set by the resource loader
    if model is not None and class_names is not None and recommendations_db is not None:
        return jsonify({"status": "ok", "message": "Model and resources loaded."}), 200
    else:
        return jsonify({"status": "error", "message": "Model or resources not loaded. Check startup logs."}), 503

# --- Testing Endpoint with HTML Form (Updated Language Options) ---
@app.route('/', methods=['GET'])
def test_predict_form():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plant Disease Predictor</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
    </style>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen p-4">
    <div class="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <h1 class="text-3xl font-bold text-center text-gray-800 mb-6">Plant Disease Predictor</h1>
        
        <form id="uploadForm" class="space-y-6">
            <div>
                <label for="imageUpload" class="block text-sm font-medium text-gray-700 mb-2">Upload Image</label>
                <input type="file" id="imageUpload" name="file" accept="image/*" class="block w-full text-sm text-gray-500
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-full file:border-0
                    file:text-sm file:font-semibold
                    file:bg-green-50 file:text-green-700
                    hover:file:bg-green-100 cursor-pointer" required>
            </div>
            
            <div class="mt-4">
                <label for="languageSelect" class="block text-sm font-medium text-gray-700 mb-2">Select Language</label>
                <select id="languageSelect" name="lang" class="block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500">
                    <option value="en">English</option>
                    <option value="ig">Igbo (Nigeria)</option>
                    <option value="yo">Yoruba (Nigeria)</option>
                    <option value="ha">Hausa (Nigeria)</option>
                    <option value="sw">Swahili</option>
                    <option value="fr">French</option>
                    <option value="es">Spanish</option>
                    <option value="de">German</option>
                </select>
            </div>
            
            <button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition duration-150 ease-in-out">
                    Predict Disease
            </button>
        </form>

        <div id="loadingIndicator" class="mt-6 text-center text-green-600 font-medium hidden">
            Processing image...
        </div>

        <div id="result" class="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200 hidden">
            <h2 class="text-lg font-semibold text-gray-800 mb-2">Prediction Result:</h2>
            <p class="text-gray-700"><strong>Class:</strong> <span id="predictedClass" class="font-bold"></span></p>
            <p class="text-gray-700"><strong>Confidence:</strong> <span id="confidence" class="font-bold"></span></p>
            <p id="message" class="text-gray-600 text-sm mt-2"></p>
            
            <div id="recommendations-section" class="mt-4">
                <h3 class="text-md font-semibold text-gray-800">Recommendations:</h3>
                <h4 class="font-medium mt-2">Overview:</h4>
                <p id="overview-text" class="text-gray-600"></p>
                
                <h4 class="font-medium mt-2">Treatment:</h4>
                <ul id="treatment-list" class="list-disc list-inside text-gray-600 pl-4"></ul>
                
                <h4 class="font-medium mt-2">Prevention:</h4>
                <ul id="prevention-list" class="list-disc list-inside text-gray-600 pl-4"></ul>
            </div>
        </div>

        <div id="error" class="mt-6 p-4 bg-red-50 rounded-lg border border-red-200 text-red-700 hidden">
            <h2 class="text-lg font-semibold mb-2">Error:</h2>
            <p id="errorMessage"></p>
        </div>
    </div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', async function(event) {
            event.preventDefault();

            const loadingIndicator = document.getElementById('loadingIndicator');
            const resultDiv = document.getElementById('result');
            const errorDiv = document.getElementById('error');
            const errorMessageSpan = document.getElementById('errorMessage');
            const messageSpan = document.getElementById('message');
            const fileInput = document.getElementById('imageUpload');
            const langSelect = document.getElementById('languageSelect');
            
            resultDiv.classList.add('hidden');
            errorDiv.classList.add('hidden');
            messageSpan.textContent = '';
            loadingIndicator.classList.remove('hidden');

            if (fileInput.files.length === 0) {
                loadingIndicator.classList.add('hidden');
                errorMessageSpan.textContent = "Please select an image file.";
                errorDiv.classList.remove('hidden');
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            try {
                // Ensure the fetch URL uses the correct port (3000)
                const response = await fetch(`/predict?lang=${langSelect.value}`, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                loadingIndicator.classList.add('hidden');

                if (response.ok) {
                    document.getElementById('predictedClass').textContent = data.predicted_class;
                    document.getElementById('confidence').textContent = (data.confidence * 100).toFixed(2) + '%';
                    
                    const overviewText = document.getElementById('overview-text');
                    const treatmentList = document.getElementById('treatment-list');
                    const preventionList = document.getElementById('prevention-list');

                    overviewText.textContent = data.recommendations.overview;
                    treatmentList.innerHTML = '';
                    data.recommendations.treatment.forEach(item => {
                        const li = document.createElement('li');
                        li.textContent = item;
                        treatmentList.appendChild(li);
                    });
                    
                    preventionList.innerHTML = '';
                    data.recommendations.prevention.forEach(item => {
                        const li = document.createElement('li');
                        li.textContent = item;
                        preventionList.appendChild(li);
                    });

                    if (data.message) {
                        messageSpan.textContent = data.message;
                    }

                    resultDiv.classList.remove('hidden');
                } else {
                    errorMessageSpan.textContent = data.error || 'Unknown error occurred.';
                    errorDiv.classList.remove('hidden');
                }
            } catch (err) {
                loadingIndicator.classList.add('hidden');
                errorMessageSpan.textContent = 'Network error or server unreachable: ' + err.message;
                errorDiv.classList.remove('hidden');
            }
        });
    </script>
</body>
</html>
""")

# --- GUNICORN ENTRY POINT ---
try:
    with app.app_context():
        load_resources()
    print("Application resources loaded successfully for Gunicorn.")
except Exception as e:
    # Log the failure but don't call exit(), let Gunicorn's worker management handle it.
    print(f"CRITICAL ERROR during app startup: {e}")