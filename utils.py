from functools import wraps
from flask import request, jsonify
import jwt
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import os

SECRET_KEY = "qwertyuiopasdfghjklzxcvbnm"

def create_jwt(data, exp_hours=12):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=exp_hours)
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_jwt(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.cookies.get("token")
        if not token:
            return jsonify({"error": "Unauthorized"}), 401
        user = decode_jwt(token)
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        request.user = user
        return f(*args, **kwargs)
    return wrapper


# --- Fernet encryption setup ---
key_file = "secret.key"

if os.path.exists(key_file):
    with open(key_file, "rb") as f:
        key = f.read()
else:
    key = Fernet.generate_key()
    with open(key_file, "wb") as f:
        f.write(key)

fernet = Fernet(key)
