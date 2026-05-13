import os, json, requests as req
from flask import Flask, request, jsonify

# ---------- ENVIRONMENT VARIABLES ----------
UPSTASH_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "https://welcomed-flounder-86019.upstash.io")
UPSTASH_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAVADAAIgcDE3ZmI1NTk4N2VmMTM0ZTExOWJiNDk5NTNmNjRkMWM1Yg")

# ---------- KV Helpers ----------
def kv_get(key):
    url = f"{UPSTASH_URL}/get/{key}"
    headers = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
    resp = req.get(url, headers=headers, timeout=5)
    if resp.status_code != 200:
        return None
    return resp.json().get("result")

# ---------- Telegram API Sender ----------
def send_photo(token, chat_id, photo_url, caption=None, reply_markup=None):
    """Telegram bot ko photo bhejne ka simple function."""
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "parse_mode": "Markdown"
    }
    if caption:
        payload["caption"] = caption
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    return req.post(url, json=payload, timeout=10)

def send_message(token, chat_id, text, reply_markup=None):
    """Simple text message with optional inline keyboard."""
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    return req.post(url, json=payload, timeout=10)

# ---------- Webhook Handler ----------
def handle_update(token, data):
    """Process a single Telegram update for a specific bot token."""
    msg = data.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = (msg.get("text") or "").strip()

    if text == "/start" and chat_id:
        config_json = kv_get(f"config:{token}")
        if config_json:
            config = json.loads(config_json)

            # 1. Photo bhejo agar URL hai
            if config.get("photo_url"):
                send_photo(token, chat_id,
                           photo_url=config["photo_url"],
                           caption=config.get("caption", ""))

            # 2. Second message with Launch button
            button_text = config.get("button_text", "🎮 Launch Game")
            button_url = config.get("button_url", "https://cryptomines.vercel.app")
            second_msg = config.get("second_message", "🌟 Ready to Start? 🌟")
            keyboard = {
                "inline_keyboard": [[
                    {"text": button_text, "web_app": {"url": button_url}}
                ]]
            }
            send_message(token, chat_id, second_msg, reply_markup=keyboard)
        else:
            # Fallback agar config nahi hai
            send_message(token, chat_id, "Welcome! Setup via Master Bot.")

# ---------- FLASK APP ----------
app = Flask(__name__)

@app.route("/api/health", methods=["GET"])
def health():
    return "Runner alive", 200

@app.route("/api/<token>", methods=["POST"])
def webhook(token):
    data = request.get_json()
    if data:
        handle_update(token, data)
    return jsonify({"ok": True})

def handler(request):
    return app(request.environ, start_response)
