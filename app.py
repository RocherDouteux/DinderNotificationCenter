from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, messaging
import os, json

app = Flask(__name__)

# Load service account key from environment variable (safer than file)
service_account_info = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred)
db = firestore.client()

API_KEY = os.environ.get("API_KEY", "super_secret_token")

@app.before_request
def check_api_key():
    key = request.headers.get("X-API-KEY")
    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

@app.route("/send_friend_request", methods=["POST"])
def send_friend_request():
    data = request.get_json()
    sender_id = data.get("senderId")
    receiver_id = data.get("receiverId")

    if not sender_id or not receiver_id:
        return jsonify({"error": "Missing senderId or receiverId"}), 400

    receiver_doc = db.collection("users").document(receiver_id).get()
    if not receiver_doc.exists:
        return jsonify({"error": "Receiver not found"}), 404

    receiver_token = receiver_doc.get("fcmToken")
    if not receiver_token:
        return jsonify({"error": "Receiver has no FCM token"}), 400

    sender_doc = db.collection("users").document(sender_id).get()
    sender_name = sender_doc.get("username") if sender_doc.exists else "Someone"

    message = messaging.Message(
        notification=messaging.Notification(
            title="New Friend Request",
            body=f"{sender_name} sent you a friend request!",
        ),
        data={"type": "friend_request", "senderId": sender_id},
        token=receiver_token,
    )

    try:
        response = messaging.send(message)
        return jsonify({"success": True, "message_id": response})
    except Exception as e:
        print("Error sending notification:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/")
def root():
    return jsonify({"status": "Dinder Push API is running!"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
