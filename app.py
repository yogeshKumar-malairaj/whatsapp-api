from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from routes.auth import auth_bp
from routes.contacts import contacts_bp
from routes.messages import messages_bp
from config import FRONTEND_ORIGINS, PORT

socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True, origins=FRONTEND_ORIGINS)

    socketio.init_app(app)

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(contacts_bp)
    app.register_blueprint(messages_bp)

    return app

# Create the app object for Gunicorn
app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=PORT, debug=True)
