from flask import Flask
from flask_cors import CORS

from .views.main import main_bp as main_blueprint
from .ml_utils import load_resources
from .firebase_utils import initialize_firebase

def create_app():
    app = Flask(__name__, template_folder='../templates')
    CORS(app)

    with app.app_context():
        load_resources()
        initialize_firebase()

    app.register_blueprint(main_blueprint)

    return app