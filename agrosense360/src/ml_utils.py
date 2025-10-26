
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from .config import MODEL_PATH, CLASS_INDICES_PATH, RECOMMENDATIONS_PATH, IMG_HEIGHT, IMG_WIDTH

# Global variables to store the loaded model and class names
model = None
class_names = None
recommendations_db = None

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
    try:
        model = load_model(MODEL_PATH, custom_objects={
            'F1Score': F1Score,
            'swish': tf.keras.activations.swish,
            'FixedDropout': FixedDropout
        })
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        # In a Gunicorn environment, we want to allow the process to fail fast
        # if a critical resource like the model cannot be loaded.
        raise RuntimeError(f"Failed to load model: {e}")

    try:
        with open(CLASS_INDICES_PATH, 'r') as f:
            loaded_indices = json.load(f)
            class_names = {int(k): v for k, v in loaded_indices.items()}
        print("Class names loaded successfully.")
    except FileNotFoundError:
        raise RuntimeError(f"Error: {CLASS_INDICES_PATH} not found.")

    try:
        with open(RECOMMENDATIONS_PATH, 'r') as f:
            recommendations_db = json.load(f)
        print("Recommendations loaded successfully.")
    except FileNotFoundError:
        raise RuntimeError(f"Error: {RECOMMENDATIONS_PATH} not found.")

def predict_image(pil_img):
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
    
    return predicted_class_name, confidence, recommendations
