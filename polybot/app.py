import os
import json
import boto3
from bot import Bot
from loguru import logger
from flask import Flask,request
from bot import TELEGRAM_TOKEN,REGION_NAME,SNS_ARN,SERVER_ENDPOINT,DYNAMO_TBL,Util

sns_client = boto3.client('sns',region_name=REGION_NAME)
dynamodb = boto3.client('dynamodb', region_name=REGION_NAME)
server_endpoint = f"{SERVER_ENDPOINT}"

app = Flask(__name__)

@app.route('/')
def statusCheck():
    return 'Ok',200

@app.route(f'/{TELEGRAM_TOKEN}',methods=["POST"])
def webhook():
    update = request.get_json()
    logger.info(f'Incoming REQ: {update}')
    bot.updater(update)
    return 'Ok',200

@app.route("/sns_update",methods=["POST"])
def sns_notification():
    data = json.loads(request.get_data().decode())
    if 'Type' in data and data['Type'] == 'SubscriptionConfirmation':
        sns_client.confirm_subscription(TopicArn=data['TopicArn'], Token=data['Token'])
        logger.info(f"Subscribed successfully with SubscriptionArn: {subscription_arn}")
    else:
        data = json.loads(data['Message'])
        if data['Status_Code'] == 200:
            response = dynamodb.get_item(
                Key={
                    '_id': {
                        'S': data['job_id'],
                    }
                },
                TableName=DYNAMO_TBL
                )
            prediction = json.loads(response['Item']['text']['S'])
            util = Util(prediction)
            result = util.object_count(prediction)
            bot.bot.send_message(data['chat_id'],result,reply_to_message_id=data['msg_id'])
        else:
            bot.bot.send_message(data['chat_id'],f"⛔️𝕊𝕠𝕞𝕖𝕥𝕙𝕚𝕟𝕘 𝕨𝕖𝕟𝕥 𝕨𝕣𝕠𝕟𝕘, 𝕖𝕚𝕥𝕙𝕖𝕣 𝕥𝕙𝕖 𝕚𝕞𝕒𝕘𝕖 𝕔𝕠𝕟𝕥𝕒𝕚𝕟𝕤 𝕟𝕠 𝕠𝕓𝕛𝕖𝕔𝕥\n𝕠𝕣 𝕥𝕙𝕖 𝕚𝕞𝕒𝕘𝕖 𝕤𝕚𝕫𝕖 𝕚𝕤 𝕥𝕠𝕠 𝕓𝕚𝕘\n𝕡𝕝𝕖𝕒𝕤𝕖 𝕥𝕣𝕪 𝕒𝕘𝕒𝕚𝕟⛔️!",reply_to_message_id=data['msg_id'])
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
try:
    response = sns_client.subscribe(
        TopicArn=SNS_ARN,
        Protocol='http',
        Endpoint=server_endpoint
    )
    subscription_arn = response['SubscriptionArn']
except Exception as e:
    logger.error(str(e))
app.run(debug=True,host="0.0.0.0",port=5000)