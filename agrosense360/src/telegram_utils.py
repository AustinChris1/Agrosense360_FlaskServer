
import requests 
from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, LANGUAGE_MAP, UI_TEXT_MAP
from .translation_utils import get_translated_ui_text

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
    if TELEGRAM_BOT_TOKEN == '7678276226:AAGNAWAFYhWIfJ6BWvld6BDki2fVDFWyb90': # Check against the placeholder token you provided
        print("WARNING: Telegram bot token is likely a placeholder. Skipping Telegram notification.")
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
