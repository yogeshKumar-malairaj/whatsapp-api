from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from db import users_col, contacts_col
from utils import create_jwt, decode_jwt, login_required
from datetime import datetime

import os

auth_bp = Blueprint("auth", __name__)

# Detect environment for cookie settings
IS_PRODUCTION = os.environ.get("FLASK_ENV") == "production"


# --- Signup ---
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.json or {}
    name = data.get("name")
    mobile_no = data.get("mobile_no")
    password = data.get("password")

    if not (name and mobile_no and password):
        return jsonify({"error": "All fields required"}), 400

    if users_col.find_one({"mobile_no": mobile_no}):
        return jsonify({"error": "Mobile number already registered"}), 400

    hashed_pw = generate_password_hash(password)

    # Insert user
    users_col.insert_one({
        "name": name,
        "mobile_no": mobile_no,
        "password": hashed_pw,
        "created_at": datetime.utcnow()
    })

    # Initialize empty contacts list
    contacts_col.insert_one({
        "owner_mobile_no": mobile_no,
        "contacts": []
    })

    # Create JWT session token
    token = create_jwt({"name": name, "mobile_no": mobile_no})

    resp = jsonify({"message": "Signup successful"})
    resp.set_cookie(
        "token",
        token,
        httponly=True,
        secure=IS_PRODUCTION,   # ✅ HTTPS in production
        samesite="None",        # ✅ Required for cross-site cookies
        max_age=7 * 24 * 60 * 60
    )

    return resp, 201


# --- Login ---
@auth_bp.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return "", 204

    data = request.json or {}
    mobile_no = data.get("mobile_no")
    password = data.get("password")

    user = users_col.find_one({"mobile_no": mobile_no})
    if not user or not check_password_hash(user.get("password", ""), password):
        return jsonify({"error": "Invalid credentials"}), 400

    payload = {
        "mobile_no": user["mobile_no"],
        "name": user["name"]
    }
    token = create_jwt(payload)

    resp = make_response(jsonify({"message": "Login successful"}))
    resp.set_cookie(
        "token",
        token,
        httponly=True,
        secure=IS_PRODUCTION,   # ✅ HTTPS only in production
        samesite="None",
        max_age=7 * 24 * 60 * 60
    )
    return resp


# --- Get Current User ---
@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    return jsonify({"user": request.user}), 200


# --- Logout ---
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    resp = jsonify({"message": "Logged out"})
    resp.delete_cookie("token")
    return resp, 200


# --- Update Profile ---
@auth_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    data = request.json or {}
    name = data.get("name")

    if not name:
        return jsonify({"error": "Name required"}), 400

    users_col.update_one({"mobile_no": request.user["mobile_no"]}, {"$set": {"name": name}})

    contacts_col.update_many(
        {"contacts.mobile_no": request.user["mobile_no"]},
        {"$set": {"contacts.$.name": name}}
    )

    return jsonify({"message": "Profile updated"}), 200


# --- Verify Token ---
@auth_bp.route("/verify-token", methods=["GET"])
def verify_token():
    token = request.cookies.get("token")
    if not token:
        return jsonify({"error": "No token"}), 401

    payload = decode_jwt(token)
    if not payload:
        return jsonify({"error": "Invalid or expired token"}), 401

    return jsonify({"message": "Valid token", "user": payload}), 200
