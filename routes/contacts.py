from flask import Blueprint, jsonify, request
from db import contacts_col, users_col, messages_col
from utils import login_required, fernet

contacts_bp = Blueprint("contacts", __name__, url_prefix="/contacts")


@contacts_bp.route("", methods=["GET"])
@login_required
def get_contacts():
    owner_mobile = request.user["mobile_no"]
    doc = contacts_col.find_one({"owner_mobile_no": owner_mobile})
    if not doc:
        return jsonify([]), 200

    contacts_list = []

    for contact in doc.get("contacts", []):
        contact_mobile = contact.get("mobile_no")
        # Fetch latest message
        latest_msg = messages_col.find({
            "$or": [
                {"from": owner_mobile, "to": contact_mobile},
                {"from": contact_mobile, "to": owner_mobile}
            ]
        }).sort("timestamp", -1).limit(1)

        latest_text = ""
        for lm in latest_msg:
            try:
                latest_text = fernet.decrypt(lm.get("text", "").encode()).decode()
            except Exception:
                latest_text = lm.get("text", "")
        
        contacts_list.append({
            "name": contact.get("name", ""),
            "mobile_no": contact_mobile,
            "latest_message": latest_text
        })

    return jsonify(contacts_list), 200


@contacts_bp.route("/add", methods=["POST"])
@login_required
def add_contact():
    data = request.json or {}
    name = data.get("name")
    mobile_no = data.get("mobile_no")

    if not (name and mobile_no):
        return jsonify({"error": "Name and mobile number required"}), 400

    if mobile_no == request.user["mobile_no"]:
        return jsonify({"error": "Cannot add yourself"}), 400

    if not users_col.find_one({"mobile_no": mobile_no}):
        return jsonify({"error": "User not found"}), 404

    # Add contact manually
    contacts_col.update_one(
        {"owner_mobile_no": request.user["mobile_no"]},
        {"$addToSet": {"contacts": {"name": name, "mobile_no": mobile_no}}},
        upsert=True
    )

    # Auto add reciprocal contact
    contact_owner_doc = contacts_col.find_one({"owner_mobile_no": mobile_no})
    if contact_owner_doc:
        contacts_col.update_one(
            {"owner_mobile_no": mobile_no},
            {"$addToSet": {"contacts": {"name": request.user["name"], "mobile_no": request.user["mobile_no"]}}}
        )

    return jsonify({"message": "Contact added"}), 201
