from flask import Flask, request
import bot

app = Flask(__name__)

@app.route('/SECRET_PATH', methods=['POST'])
def webhook():
    update = request.get_json()
    bot.handle_update(update)
    return "", 200
