from flask import Blueprint, request, jsonify
from db import processed_messages_col
from datetime import datetime

webhook_bp = Blueprint("webhook", __name__, url_prefix="/webhook")

@webhook_bp.route("/payload", methods=["POST"])
def process_payload():
    payload = request.json
    # Basic sample processing:
    # Insert message if new
    # Update status if existing

    # Your parsing and insert/update logic here
    
    return jsonify({"status": "processed"})
