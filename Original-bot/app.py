import json
import boto3
import loguru
from bot import Bot
from flask import Flask, request
from bot import token, region_name, sns_topic_arn, server_endpoint, table, Util

app = Flask(__name__)

sns_client = boto3.client("sns", region_name=region_name)
dynamodb = boto3.resource("dynamodb", region_name=region_name)
server_endpoint = server_endpoint


@app.route("/")
def statusCheck():
    return "Ok", 200


@app.route(f"/{token}", methods=["POST"])
def webhook():
    update = request.get_json()
    bot.updater(update)
    return "Ok", 200


@app.route("/sns_update", methods=["POST"])
def sns_notification():
    data = json.loads(request.get_data().decode())
    if "Type" in data and data["Type"] == "SubscriptionConfirmation":
        sns_client.confirm_subscription(TopicArn=data["TopicArn"], Token=data["Token"])
        loguru.logger.info(
            f"Subscribed successfully with SubscriptionArn: {subscription_arn}"
        )
    else:
        data = json.loads(data["Message"])
        if data["Status_Code"] == 200:
            table_resource = dynamodb.Table(table)
            response = table_resource.get_item(
                Key={
                    "_id": data["job_id"]
                }
            )
            prediction = json.loads(response["Item"]["text"])
            util = Util(prediction)
            result = util.object_count()
            bot.bot.send_message(
                data["chat_id"], result, reply_to_message_id=data["msg_id"]
            )
        else:
            bot.bot.send_message(
                data["chat_id"],
                "Something went wrong, either the image is too big\nor no objects were detected in the image.",
                reply_to_message_id=data["msg_id"],
            )
    return "Ok", 200


bot = Bot()
bot.startCommand()
bot.getHelp()
bot.callback()
bot.text_handler()
bot.photo_handler()

try:
    response = sns_client.subscribe(
        TopicArn=sns_topic_arn, Protocol="https", Endpoint=server_endpoint
    )
    subscription_arn = response["SubscriptionArn"]
except Exception as e:
    loguru.logger.error(str(e))

app.run(debug=True, host="0.0.0.0", port=5000)
