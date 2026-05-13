import os, json, requests as req, asyncio
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

UPSTASH_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "https://welcomed-flounder-86019.upstash.io")
UPSTASH_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAVADAAIgcDE3ZmI1NTk4N2VmMTM0ZTExOWJiNDk5NTNmNjRkMWM1Yg")

def kv_get(key):
    url = f"{UPSTASH_URL}/get/{key}"
    headers = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
    resp = req.get(url, headers=headers, timeout=5)
    if resp.status_code != 200:
        return None
    return resp.json().get("result")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = context.bot.token
    config_json = kv_get(f"config:{token}")
    if config_json:
        config = json.loads(config_json)
        if config.get("photo_url"):
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=config["photo_url"],
                caption=config.get("caption", ""),
                parse_mode="Markdown"
            )
        second_msg = config.get("second_message", "🌟 Ready to Start? 🌟")
        button_text = config.get("button_text", "🎮 Launch Game")
        button_url = config.get("button_url", "https://cryptomines.vercel.app")
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(button_text, web_app=WebAppInfo(url=button_url))
        ]])
        await update.message.reply_text(second_msg, reply_markup=keyboard)
    else:
        await update.message.reply_text("Welcome! Setup via Master Bot.")

app = Flask(__name__)

# ✅ Ab /api/health hi call hoga
@app.route("/health", methods=["GET"])
def health():
    return "Runner alive", 200

# ✅ /api/<token> hi call hoga
@app.route("/<token>", methods=["POST"])
def webhook(token):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        data = request.get_json()
        application = Application.builder().token(token).build()
        application.add_handler(CommandHandler("start", start))
        loop.run_until_complete(application.initialize())
        update = Update.de_json(data, application.bot)
        loop.run_until_complete(application.process_update(update))
        loop.run_until_complete(application.shutdown())
        return jsonify({"ok": True})
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        loop.close()

def handler(request):
    return app(request.environ, start_response)
