from flask import Flask,request
import os
app = Flask(__name__)
from bot import Bot

token = os.environ['TELEGRAM_TOKEN']

@app.route(f'/{token}',methods=["POST"])
def webhook():
    update = request.get_json()
    bot.updater(update)
    return 'Ok',200

bot = Bot()
bot.startCommand()
bot.getHelp()
bot.callback()
bot.text_handler()
bot.photo_handler()
app.run(debug=True,host="0.0.0.0",port=5000)
