#!/bin/bash
set -e

echo "🚀 Starting setup..."

# 1️⃣ Install dependencies
if [ -f "requirements.txt" ]; then
    echo "✅ Installing dependencies..."
    pip install --no-cache-dir -r requirements.txt
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# 2️⃣ Download model if missing
if [ ! -f "best_agrosense_model.h5" ]; then
    echo "⬇️ Downloading model from Google Drive..."
    FILE_ID="1xkvaONSV_Y5i4uts6qWYxesaf5LAH7Ll"
    wget --no-check-certificate "https://drive.google.com/uc?export=download&id=${FILE_ID}" -O best_agrosense_model.h5
fi

# 3️⃣ Download Firebase key if missing
if [ ! -f "firebase_service_account.json" ]; then
    echo "⬇️ Downloading Firebase service account file..."
    FIREBASE_FILE_ID="14Ejyhtvk27B1UTMxrh8OjvtvebgyS51g"
    wget --no-check-certificate "https://drive.google.com/uc?export=download&id=${FIREBASE_FILE_ID}" -O firebase_service_account.json
fi

# 4️⃣ Start Flask app directly (no Docker, no Gunicorn)
echo "🚀 Starting Flask app on port ${PORT:-8080}..."
flask run --host=0.0.0.0 --port=${PORT:-8080}
