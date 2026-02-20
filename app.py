import os
import json
import hmac
import hashlib
from flask import Flask, request, abort
from telegram import Bot
import razorpay

# ================== CONFIG ==================

BOT_TOKEN = os.environ.get("8416145274:AAHQxyREWJYGsIqOOlSVKtEkeBS076iEcfI")
RAZORPAY_KEY_ID = os.environ.get("rzp_test_SINKbNwzFjDr4w")
RAZORPAY_KEY_SECRET = os.environ.get("gH4mUJpVWAUa690wvp2SLkUS")
WEBHOOK_SECRET = os.environ.get("WE—>The@king#94")

VIDEO_FILE_ID = "BAACAgUAAxkBAAMVaZi17-4vMKxg-Y2TO5sIjERe5TAAAr4YAAKz6slU5rq7yc7rx6s6BA"
PRICE = 3900  # 39 INR = 3900 paise

bot = Bot(token=BOT_TOKEN)
razorpay_client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)

app = Flask(__name__)

# ================== HELPERS ==================

def load_data():
    with open("data.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f)

# ================== TELEGRAM START ==================

@app.route("/")
def home():
    return "Bot is running"

# ================== CREATE ORDER ==================

@app.route("/create-order", methods=["POST"])
def create_order():
    data = request.json
    user_id = str(data["user_id"])

    order = razorpay_client.order.create({
        "amount": PRICE,
        "currency": "INR",
        "payment_capture": 1
    })

    db = load_data()
    db[order["id"]] = {
        "user_id": user_id,
        "status": "pending"
    }
    save_data(db)

    return {"order_id": order["id"]}

# ================== RAZORPAY WEBHOOK ==================

@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    payload = request.data
    signature = request.headers.get("X-Razorpay-Signature")

    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

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

            bot.send_video(
                chat_id=user_id,
                video=VIDEO_FILE_ID,
                caption="✅ Payment Successful!\n🎬 Here is your full video",
                protect_content=True
            )

    return "OK"

# ================== RUN ==================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
