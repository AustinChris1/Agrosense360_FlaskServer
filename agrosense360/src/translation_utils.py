
from googletrans import Translator 

translator = Translator()

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
