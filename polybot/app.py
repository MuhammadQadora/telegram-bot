import os
from bot import Bot
from loguru import logger
from flask import Flask,request
from bot import TELEGRAM_TOKEN

app = Flask(__name__)

@app.route(f'/{TELEGRAM_TOKEN}',methods=["POST"])
def webhook():
    update = request.get_json()
    logger.info(f'Incoming REQ: {update}')
    bot.updater(update)
    return 'Ok',200

bot = Bot()
bot.startCommand()
bot.getVersion()
bot.getCloseGPT()
bot.getPhoto()
bot.getHelp()
bot.getOpions()
bot.getVideo()
bot.getText()
app.run(debug=True,host="0.0.0.0",port=5000)