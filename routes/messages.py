from flask import Blueprint, request, jsonify
from db import messages_col, contacts_col
from utils import login_required, fernet
from datetime import datetime
from extensions import socketio

messages_bp = Blueprint("messages", __name__, url_prefix="/messages")


@messages_bp.route("/send", methods=["POST"])
@login_required
def send_message():
    data = request.json
    to = data.get("to")
    text = data.get("text")

    if not (to and text):
        return jsonify({"error": "Recipient and text required"}), 400

    # Encrypt for DB
    encrypted_text = fernet.encrypt(text.encode()).decode()
    timestamp = datetime.utcnow()

    msg = {
        "from": request.user["mobile_no"],
        "to": to,
        "text": encrypted_text,
        "timestamp": timestamp,
        "status": "sent"
    }

    messages_col.insert_one(msg)

    # --- Auto-add contacts for both sides ---
    for owner, contact_mobile in [(msg["from"], msg["to"]), (msg["to"], msg["from"])]:
        doc = contacts_col.find_one({"owner_mobile_no": owner})
        if not doc:
            contacts_col.insert_one({
                "owner_mobile_no": owner,
                "contacts": [{"mobile_no": contact_mobile, "name": ""}]
            })
        else:
            if not any(c["mobile_no"] == contact_mobile for c in doc.get("contacts", [])):
                contacts_col.update_one(
                    {"owner_mobile_no": owner},
                    {"$push": {"contacts": {"mobile_no": contact_mobile, "name": ""}}}
                )

    # Prepare decrypted version for frontend/socket
    msg_for_socket = {
        "from": msg["from"],
        "to": msg["to"],
        "text": text,
        "timestamp": timestamp.isoformat(),
        "status": "sent"
    }

    socketio.emit("new_message", msg_for_socket, room=to)
    socketio.emit("new_message", msg_for_socket, room=msg["from"])

    return jsonify({"message": "Sent"}), 201


@messages_bp.route("/messages/<mobile_no>", methods=["GET"])
@login_required
def get_messages(mobile_no):
    owner = request.user["mobile_no"]

    docs = list(messages_col.find({
        "$or": [
            {"from": owner, "to": mobile_no},
            {"from": mobile_no, "to": owner}
        ]
    }).sort("timestamp", 1))

    out = []
    unread_ids = []

    for m in docs:
        text = m.get("text")
        try:
            text = fernet.decrypt(text.encode()).decode()
        except Exception:
            pass

        ts = m.get("timestamp")
        if isinstance(ts, datetime):
            ts = ts.isoformat()

        out.append({
            "_id": str(m["_id"]),
            "from": m.get("from"),
            "to": m.get("to"),
            "text": text,
            "timestamp": ts,
            "status": m.get("status", "sent")
        })

        if m.get("to") == owner and m.get("status") == "sent":
            unread_ids.append(m["_id"])

    if unread_ids:
        messages_col.update_many(
            {"_id": {"$in": unread_ids}},
            {"$set": {"status": "delivered"}}
        )

    return jsonify(out), 200
