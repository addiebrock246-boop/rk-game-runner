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

# ---------- Telegram API sender (no external libs) ----------
def send_photo(token, chat_id, photo_url, caption=None, reply_markup=None):
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
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    return req.post(url, json=payload, timeout=10)

# ---------- Core Logic ----------
def handle_update(token, data):
    msg = data.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = (msg.get("text") or "").strip()

    if text == "/start" and chat_id:
        config_json = kv_get(f"config:{token}")
        if config_json:
            config = json.loads(config_json)
            # Photo (if exists)
            if config.get("photo_url"):
                send_photo(token, chat_id,
                           photo_url=config["photo_url"],
                           caption=config.get("caption", ""))
            # Second message with button
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
            send_message(token, chat_id, "Welcome! Setup via Master Bot.")

# ---------- Flask App with Catch‑All Route ----------
app = Flask(__name__)

# Catch‑all: har path yahan aayega, hum decide karenge
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    # Vercel request ka full path (e.g., /api/health, /api/<token>, ya seedha health, <token>)
    full_path = "/" + path
    # Health check (chahe /api/health aaye ya /health)
    if full_path.endswith("/api/health") or full_path.endswith("/health") or path == "health":
        return "Runner alive", 200

    # Webhook: agar path kuch is tarah se aaye /api/<token>, /<token>
    # Token nikaalne ki trick: path ke aakhri segment ko le lenge jo ':' contain kare
    parts = full_path.strip("/").split("/")
    token = None
    for part in parts:
        if ":" in part and len(part) > 20:   # Telegram token pattern
            token = part
            break

    if request.method == "POST" and token:
        data = request.get_json()
        if data:
            handle_update(token, data)
            return jsonify({"ok": True})
    return "Not Found", 404

def handler(request):
    return app(request.environ, start_response)
