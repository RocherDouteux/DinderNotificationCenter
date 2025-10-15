from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, messaging, auth
import os, json

app = Flask(__name__)

# Load service account key from environment variable (safer than file)
service_account_info = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred)
db = firestore.client()

def json_error(status, code, message):
    return jsonify({"error": {"code": code, "message": message}}), status

def verify_id_token_from_header():
    """
    Expects: Authorization: Bearer <Firebase ID token>
    Returns decoded token dict or an error response.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, json_error(401, "unauthenticated", "Missing Authorization Bearer token.")
    token = auth_header.split(" ", 1)[1].strip()
    try:
        decoded = auth.verify_id_token(token, check_revoked=True)
        return decoded, None
    except auth.ExpiredIdTokenError:
        return None, json_error(401, "unauthenticated", "Expired ID token.")
    except auth.RevokedIdTokenError:
        return None, json_error(401, "unauthenticated", "Revoked ID token.")
    except Exception:
        return None, json_error(401, "unauthenticated", "Invalid ID token.")

@app.route("/send_friend_request", methods=["POST"])
def send_friend_request():
    # Verify caller identity
    decoded, err = verify_id_token_from_header()
    if err:
        return err
    caller_uid = decoded["uid"]

    data = request.get_json(silent=True) or {}
    sender_id = data.get("senderId")
    receiver_id = data.get("receiverId")

    if not sender_id or not receiver_id:
        return json_error(400, "bad_request", "Missing senderId or receiverId.")

    # Optional but recommended: ensure the caller is the claimed sender
    if caller_uid != sender_id:
        return json_error(403, "forbidden", "Caller does not match senderId.")

    receiver_doc = db.collection("users").document(receiver_id).get()
    if not receiver_doc.exists:
        return json_error(404, "not_found", "Receiver not found.")

    receiver_token = receiver_doc.get("fcmToken")
    if not receiver_token:
        return json_error(400, "no_target_token", "Receiver has no FCM token.")

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
        return jsonify({"success": True, "message_id": response}), 200
    except Exception as e:
        print("Error sending notification:", e)
        return json_error(500, "fcm_error", str(e))

@app.route("/")
def root():
    return jsonify({"status": "Dinder Push API is running!"})

if __name__ == "__main__":
    # Use gunicorn in production; this is fine for local/dev.
    app.run(host="0.0.0.0", port=5000)
