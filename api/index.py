from flask import Flask, request, jsonify
import requests as req

BOT_TOKEN = "8870427358:AAFeiXpIQ8JnYs8ZVZ_6Vbzvcj1GTjVwMKg"

app = Flask(__name__)

@app.route("/api", methods=["POST"])
def webhook():
    data = request.get_json()
    msg = data.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "")

    if chat_id and text:
        reply = f"Tera message: {text}"
        req.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": reply}
        )

    return jsonify({"ok": True})

def handler(request):
    return app(request.environ, start_response)
