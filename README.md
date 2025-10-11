# DinderNotificationCenter

**DinderNotificationCenter** is a lightweight Flask-based microservice that handles **Firebase Cloud Messaging (FCM)** push notifications for the Dinder app.  
It listens for friend request events and sends real-time push notifications to the receiver’s device — even when the app is closed.

---

## Features

- **Push Notifications** via Firebase Cloud Messaging (FCM)  
- **Secure Access** using an API key or Firebase Auth verification  
- **Deployable on Render (Free Tier)** — zero cost, no Functions required  
- **Configurable** through environment variables  
- **Firebase Admin SDK** integration for direct Firestore + Messaging access  

---

## Project Structure

```
DinderNotificationCenter/
 ├─ app.py                  # Flask API entry point
 ├─ requirements.txt        # Python dependencies
 ├─ .gitignore              # Ignore compiled and sensitive files
 └─ README.md               # You are here
```

---

## Setup

### Prerequisites

- [Python 3.10+](https://www.python.org/)
- A [Firebase project](https://console.firebase.google.com/)
- A **Service Account Key** (JSON file) from  
  `Firebase Console → Project Settings → Service Accounts → Generate new private key`

---

###Install dependencies

```bash
pip install -r requirements.txt
```

---

###  ️Environment variables

Before running the server, set the following environment variables:

| Name | Description |
|------|--------------|
| `FIREBASE_SERVICE_ACCOUNT` | The full JSON content of your Firebase Admin key |
| `API_KEY` | Secret token required to access the API (e.g. `s3cr3t_dinder_key_123`) |

Example (Linux/macOS):
```bash
export FIREBASE_SERVICE_ACCOUNT="$(cat serviceAccountKey.json)"
export API_KEY="s3cr3t_dinder_key_123"
```

---

### Run locally

```bash
python app.py
```

Visit [http://localhost:5000](http://localhost:5000) to confirm it’s running:
```json
{ "status": "Dinder Push API is running!" }
```

---

## Deploying on Render

1. Push this repository to GitHub  
2. On [Render.com](https://render.com):
   - Create a **new Web Service**
   - Connect your repo
   - Build command:  
     ```
     pip install -r requirements.txt
     ```
   - Start command:  
     ```
     gunicorn app:app
     ```
3. Add the same environment variables (`FIREBASE_SERVICE_ACCOUNT`, `API_KEY`)
4. Deploy !  

Render will host your Flask API securely over HTTPS.

---

## API Reference

### `POST /send_friend_request`

**Description:**  
Sends a push notification when a new friend request is created.

**Headers:**
```
Content-Type: application/json
X-API-KEY: <your API key>
```

**Body:**
```json
{
  "senderId": "abc123",
  "receiverId": "xyz789"
}
```

**Response:**
```json
{
  "success": true,
  "message_id": "projects/.../messages/..."
}
```

---

## How it Works

1. The Dinder app sends a POST request to `/send_friend_request`
2. The service fetches the receiver’s `fcmToken` from Firestore
3. It builds a Firebase Cloud Message payload
4. FCM delivers the push to the receiver’s device

---

## Security

- Service Account key is never stored in code — it’s loaded from an environment variable.  
- The API is protected by an `X-API-KEY` header (or can use Firebase ID token verification).  
- HTTPS enforced by Render.  

---

## Testing

```bash
curl -X POST https://dinder-push-api.onrender.com/send_friend_request   -H "Content-Type: application/json"   -H "X-API-KEY: s3cr3t_dinder_key_123"   -d '{"senderId":"user1","receiverId":"user2"}'
```

You should see:
```json
{ "success": true, "message_id": "..." }
```

