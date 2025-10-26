
from flask import Blueprint, request, jsonify, render_template
from PIL import Image
from io import BytesIO
import tensorflow as tf


from ..ml_utils import predict_image, model, class_names, recommendations_db
from ..image_utils import is_low_quality_image, is_leaf_detected
from ..translation_utils import translate_text
from ..firebase_utils import push_prediction_to_firebase
from ..telegram_utils import create_telegram_message, send_telegram_photo
from ..config import LANGUAGE_MAP

main_bp = Blueprint('main', __name__)

@main_bp.route('/predict', methods=['POST'])
def predict_endpoint():
    if 'file' not in request.files:
        return jsonify({"error": "No image file provided."}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected image file."}), 400
    
    dest_lang = request.args.get('lang', 'en').lower()
    
    if file:
        try:
            if model is None:
                 return jsonify({"error": "Model not yet loaded. Server is initializing."}), 503
                 
            pil_img = Image.open(file.stream).convert('RGB')

            if is_low_quality_image(pil_img):
                return jsonify({"error": "Image quality is too low (e.g., too dark, too uniform). Please upload a clearer image."}), 400
            
            if not is_leaf_detected(pil_img):
                return jsonify({"error": "No significant plant leaf detected in the image. Please upload an image of a plant leaf."}), 400

            predicted_class_name, confidence, recommendations = predict_image(pil_img)

            translated_recommendations = {
                "overview": translate_text(recommendations["overview"], dest_lang),
                "treatment": translate_text(recommendations["treatment"], dest_lang),
                "prevention": translate_text(recommendations["prevention"], dest_lang)
            }
            
            full_language_name = LANGUAGE_MAP.get(dest_lang, dest_lang.upper())
            translated_recommendations['language'] = dest_lang
            translated_recommendations['language_name'] = full_language_name

            firebase_data = {
                "timestamp": tf.timestamp().numpy().tolist(),
                "predicted_class": predicted_class_name,
                "confidence": confidence,
                "recommendations": translated_recommendations
            }

            push_prediction_to_firebase(firebase_data)
            
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

@main_bp.route('/health', methods=['GET'])
def health_check():
    if model is not None and class_names is not None and recommendations_db is not None:
        return jsonify({"status": "ok", "message": "Model and resources loaded."}), 200
    else:
        return jsonify({"status": "error", "message": "Model or resources not loaded. Check startup logs."}), 503

@main_bp.route('/', methods=['GET'])
def test_predict_form():
    return render_template('index.html')
