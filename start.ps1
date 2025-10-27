Write-Host "🚀 Starting setup..."

# 1️⃣ Requirements
if (Test-Path "requirements.txt") {
    Write-Host "✅ Installing dependencies..."
    pip install -r requirements.txt
} else {
    Write-Host "❌ ERROR: requirements.txt not found. Build cannot continue."
    exit 1
}

# 2️⃣Already downloaded ModelDownload
# Write-Host "⬇️ Downloading model from Google Drive..."
# $FILE_ID = "1xkvaONSV_Y5i4uts6qWYxesaf5LAH7Ll"
# $FILE_NAME = "best_agrosense_model.h5"
# Invoke-WebRequest -Uri "https://drive.google.com/uc?export=download&id=$FILE_ID" -OutFile $FILE_NAME
# if ((Get-Item $FILE_NAME).Length -gt 0) {
#     Write-Host "✅ Model download complete: $FILE_NAME"
# } else {
#     Write-Host "❌ ERROR: Model file failed to download or is empty!"
#     exit 1
# }

# 3️⃣ Firebase Key
# Write-Host "⬇️ Downloading Firebase service account file..."
# $FIREBASE_FILE_ID = "14Ejyhtvk27B1UTMxrh8OjvtvebgyS51g"
# $FIREBASE_FILE_NAME = "firebase_service_account.json"
# Invoke-WebRequest -Uri "https://drive.google.com/uc?export=download&id=$FIREBASE_FILE_ID" -OutFile $FIREBASE_FILE_NAME
# if ((Get-Item $FIREBASE_FILE_NAME).Length -gt 0) {
#     Write-Host "✅ Firebase key downloaded successfully: $FIREBASE_FILE_NAME"
# } else {
#     Write-Host "❌ ERROR: Firebase key failed to download or is empty!"
#     exit 1
# }

# 4️⃣ Start Flask
Write-Host "🚀 Starting Flask app..."
flask run --host 0.0.0.0 --port 8080
