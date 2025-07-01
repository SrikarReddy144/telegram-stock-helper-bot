from flask import Flask, request
import telegram
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

@app.route(f"/{os.getenv('SECRET_PATH')}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    return "ok"

# Optional for local testing
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
