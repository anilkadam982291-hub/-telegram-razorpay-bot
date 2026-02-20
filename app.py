import os
import json
import hmac
import hashlib
from flask import Flask, request, abort
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import razorpay

# ================== CONFIG ==================
BOT_TOKEN = os.environ.get("8416145274:AAHQxyREWJYGsIqOOlSVKtEkeBS076iEcfI")
RAZORPAY_KEY_ID = os.environ.get("rzp_test_SINKbNwzFjDr4w")
RAZORPAY_KEY_SECRET = os.environ.get("gH4mUJpVWAUa690wvp2SLkUS")
WEBHOOK_SECRET = os.environ.get("WE—>The@king#94")

VIDEO_FILE_ID = "BAACAgUAAxkBAAMVaZi17-4vMKxg-Y2TO5sIjERe5TAAAr4YAAKz6slU5rq7yc7rx6s6BA"
THUMBNAIL_FILE_ID = "AgACAgUAAxkBAAMaaZjIZyrwR2Z5asP3N8YeusNxrIAAAnwNaxuz6slUirkLaKyvubQBAAMCAAN5AAM6BA"
PRICE = 3900  # 39 INR = 3900 paise

bot = Bot(token=BOT_TOKEN)
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
app = Flask(__name__)

# ================== DATABASE ==================
def load_data():
    with open("data.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f)

# ================== TELEGRAM WEBHOOK ==================
@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    update = request.json
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        # /start command
        if text == "/start":
            caption = "🎬 Here is the video you want!\n\nClick below to pay ₹39 and get full access."
            keyboard = [[InlineKeyboardButton("Pay ₹39", callback_data="pay")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            bot.send_photo(chat_id=chat_id, photo=THUMBNAIL_FILE_ID, caption=caption, reply_markup=reply_markup)

    # Button click (callback_query)
    elif "callback_query" in update:
        callback = update["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        data = callback["data"]

        if data == "pay":
            # Create Razorpay order
            order = razorpay_client.order.create({
                "amount": PRICE,
                "currency": "INR",
                "payment_capture": 1
            })

            db = load_data()
            db[order["id"]] = {"user_id": chat_id, "status": "pending"}
            save_data(db)

            bot.send_message(chat_id=chat_id, text=f"✅ Order created! Order ID: {order['id']}\nPay using Razorpay link (test mode).")

    return "OK"

# ================== RAZORPAY WEBHOOK ==================
@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    payload = request.data
    signature = request.headers.get("X-Razorpay-Signature")
    expected_signature = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        abort(400)

    event = request.json
    if event["event"] == "payment.captured":
        order_id = event["payload"]["payment"]["entity"]["order_id"]

        db = load_data()
        if order_id in db:
            user_id = int(db[order_id]["user_id"])
            db[order_id]["status"] = "paid"
            save_data(db)

            bot.send_video(chat_id=user_id, video=VIDEO_FILE_ID,
                           caption="✅ Payment Successful!\n🎬 Here is your full video",
                           protect_content=True)
    return "OK"

# ================== RUN ==================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
