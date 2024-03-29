import json
from flask import Flask,request
import os
app = Flask(__name__)
import boto3
from bot import Bot
import loguru
from bot import token,region_name, sns_topic_arn, yolo_url,table,Util


sns_client = boto3.client('sns',region_name=region_name)
dynamodb = boto3.client('dynamodb', region_name=region_name)
server_endpoint = f"{yolo_url}/sns_update"

@app.route(f'/{token}',methods=["POST"])
def webhook():
    update = request.get_json()
    bot.updater(update)
    return 'Ok',200

#result = {'job_id': msg_id,"msg": message['chat_id'], 'Status_Code': 200}
@app.route("/sns_update",methods=["POST"])
def sns_notification():
    data = request.get_json()
    loguru.logger(data)
    if 'Type' in data and data['Type'] == 'SubscriptionConfirmation':
        sns_client.confirm_subscription(TopicArn=data['TopicArn'], Token=data['Token'])
        loguru.logger.info(f"Subscribed successfully with SubscriptionArn: {sns_topic_arn}")
    data = json.load(data['Message'])
    if 200 in data['Status_Code']:
        response = dynamodb.get_item(
            Key={
                '_id': {
                    'S': data['job_id'],
                }
            },
            TableName=table
            )
        prediction = json.loads(response['Item']['text']['S'])
        util = Util()
        result = util.object_count(prediction)
        bot.bot.reply_to(data['msg'],result)
    else:
        bot.bot.reply_to(data['msg'],"Something went wrong, either the image is too big\nor no objects were detected in the image.")

bot = Bot()
bot.startCommand()
bot.getHelp()
bot.callback()
bot.text_handler()
bot.photo_handler()

try:
    response = sns_client.subscribe(
        TopicArn=sns_topic_arn,
        Protocol='https',
        Endpoint=server_endpoint
    )
    subscription_arn = response['SubscriptionArn']
except Exception as e:
    loguru.logger.error(str(e))
app.run(debug=True,host="0.0.0.0",port=5000)
