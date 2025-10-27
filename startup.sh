#!/bin/bash
set -e

echo "🚀 Starting Flask initialization..."

# 1. Requirements
if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt found, installing dependencies..."
    pip install --no-cache-dir -r requirements.txt
else
    echo "❌ ERROR: requirements.txt not found. Exiting."
    exit 1
fi

# 2. Model
echo "⬇️ Downloading model from Google Drive..."
FILE_ID="1xkvaONSV_Y5i4uts6qWYxesaf5LAH7Ll"
FILE_NAME="best_agrosense_model.h5"
wget --no-check-certificate "https://drive.google.com/uc?export=download&id=${FILE_ID}" -O "${FILE_NAME}"
if [ -s "${FILE_NAME}" ]; then
    echo "✅ Model downloaded: ${FILE_NAME}"
else
    echo "❌ ERROR: Model file failed to download or is empty!"
    exit 1
fi

# 3. Firebase
echo "⬇️ Downloading Firebase service account file..."
FIREBASE_FILE_ID="14Ejyhtvk27B1UTMxrh8OjvtvebgyS51g"
FIREBASE_FILE_NAME="firebase_service_account.json"
wget --no-check-certificate "https://drive.google.com/uc?export=download&id=${FIREBASE_FILE_ID}" -O "${FIREBASE_FILE_NAME}"
if [ -s "${FIREBASE_FILE_NAME}" ]; then
    echo "✅ Firebase key downloaded: ${FIREBASE_FILE_NAME}"
else
    echo "❌ ERROR: Firebase key failed to download or is empty!"
    exit 1
fi

# 4. Start Flask
echo "🔥 Starting Flask app..."
flask run --host=0.0.0.0 --port=${PORT:-8080}
