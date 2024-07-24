import telebot
import telebot.types
from io import BytesIO
import os
from loguru import logger
import boto3
import botocore.exceptions
import time
from openAi import AI
from sec import secret_keys
import json
from dynamodbAPI import dynamodbAPI
from flags_user_DB import *

# ##################
# token = os.environ["TELEGRAM_TOKEN"]
# url = os.environ["TELEGRAM_APP_URL"]
# bucket_name = secret_keys["BUCKET_NAME"]
# queue_url = os.environ["SQS_URL"]
# region_name = os.environ["REGION_NAME"]
# sns_topic_arn = os.environ["SNS_ARN"]
# table = os.environ["DYNAMO_TBL"]
# server_endpoint = os.environ["SERVER_ENDPOINT"]
# #######################

# sqs_client = boto3.client("sqs", region_name=region_name)

# ########################

##################
token = "7164236172:AAEmrU7Ie8uq8K2Duhm-wYjtqj_XfcaKHQ0"
url = "https://48fa-37-122-152-206.ngrok-free.app"
bucket_name = secret_keys["BUCKET_NAME"]
queue_url = "telegrambot-yolo5-mf"
region_name = "us-east-1"
sns_topic_arn = "arn:aws:sns:us-east-1:933060838752:telegrambot-sns-mf"
table = "telegrambot-mf"
server_endpoint = "https://48fa-37-122-152-206.ngrok-free.app/sns_update"
#######################

sqs_client = boto3.client("sqs", region_name=region_name)

########################


class Util:
    def __init__(self, json_data):
        self.json_data = json_data

    def object_count(self):
        total_items = len(self.json_data["labels"])
        print(f"There are {total_items} items in the JSON")
        class_count = {}
        for item in self.json_data["labels"]:
            class_name = item["class"]
            if class_name in class_count:
                class_count[class_name] += 1
            else:
                class_count[class_name] = 1
        if len(class_count) == 0:
            return "Zero objects Detected :("
        else:
            result = "Detected Objects:\n"
            for key, val in class_count.items():
                result += f"{key}: {val}\n"
            return result

async def send_animation(bot, chat_id, processing_function):
    gif_path = os.path.join(os.path.dirname(__file__), 'GIF', 'loading.gif')
    try:
        with open(gif_path, "rb") as gif_file:
            # Send the GIF animation and save the message ID
            animation_msg = await bot.send_animation(chat_id, gif_file)

        # Perform the processing
        result = await processing_function()

        # Send the final response
        await bot.send_message(chat_id=chat_id, text=result)

        # Optionally, delete the animation message if no longer needed
        await bot.delete_message(chat_id=chat_id, message_id=animation_msg.message_id)

    except Exception as e:
        print(f"Failed to send GIF or response message: {e}")
        logger.error(f"Failed to send GIF or response message: {e}")


class Bot:
    # Initiate connection with telegram
    def __init__(self):
        self.bot = telebot.TeleBot(token=token)
        self.bot.remove_webhook()
        time.sleep(5)
        self.bot.set_webhook(f"{url}/{token}", timeout=60)
        logger.info(f"Connected to bot:\n{self.bot.get_me()}")
        self.chatgpt = AI()

    # this function continuously checks for comming messages
    def updater(self, request):
        update = telebot.types.Update.de_json(request)
        self.bot.process_new_updates([update])

    # This function responds with a greeting when the user uses /start
    def startCommand(self):
        @self.bot.message_handler(commands=["start"])
        def start(msg):
            gif_path = os.path.join(os.path.dirname(__file__), 'GIF', 'loading.gif')
            try:
                with open(gif_path, "rb") as gif_file:
                    # Send the GIF animation and save the message ID
                    animation_msg = self.bot.send_animation(
                        msg.chat.id,
                        gif_file
                    )
                
                # Simulate processing
                time.sleep(5)  # Replace with actual processing logic
                
                # Send the final response
                self.bot.send_message(
                    chat_id=msg.chat.id,
                    text=f"This is a placeholder for the actual response."
                )
                
                # Optionally, delete the animation message if no longer needed
                self.bot.delete_message(
                    chat_id=msg.chat.id,
                    message_id=animation_msg.message_id
                )
            except Exception as e:
                print(f"Failed to send GIF or response message: {e}")
                logger.error(f"Failed to send GIF or response message: {e}")
            # self.bot.send_message(
            #     msg.chat.id,
            #     f"Hi there {msg.from_user.first_name}.\nWelcome to my amazing bot,\nTo see what this Bot can do use /options .",
            # )
            # if not is_member_in_list_by_name(msg.chat.id):
            #     add_member(msg.chat.id)


    # This function responds to add '/quit' button
    def addReplayKeyboard(self, chat_id):
        keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        item_options = telebot.types.KeyboardButton('/quit')
        keyboard.add(item_options)

        self.bot.send_message(
            chat_id,
            "Chat With GPT-4o Activated", reply_markup=keyboard)
        return keyboard

    # This function responds to remove '/quit' button
    def removeReplyKeyboard(self, chat_id):
        markup = telebot.types.ReplyKeyboardRemove()
        self.bot.send_message(chat_id, "Chat With GPT-4o Deactivated", reply_markup=markup)

    # This function responds with a greeting when the user uses /options
    def getHelp(self):
        @self.bot.message_handler(commands=["options"])
        def help(msg):
            if is_member_in_list_by_name(msg.chat.id):
                member = get_member_from_dynamo(name=msg.chat.id)
                for notification in member.notify:
                    member.notify[notification] = False
            else:
                add_member(msg.chat.id)
            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            gpt_4 = telebot.types.InlineKeyboardButton(
                "Chat with GPT-4o", callback_data="answer_gpt4"
            )
            yolov5 = telebot.types.InlineKeyboardButton(
                "Object Detection", callback_data="answer_yolov5"
            )
            text_to_image = telebot.types.InlineKeyboardButton(
                "Text to Image", callback_data="answer_imageToText"
            )
            gpt_one_question = telebot.types.InlineKeyboardButton(
                "Ask a question", callback_data="answer_question"
            )
            markup.add(gpt_4, yolov5, gpt_one_question, text_to_image)
            self.bot.send_message(
                msg.chat.id, "Available Options", reply_markup=markup)

    # This function receives photos, uploads them to s3, posts them to Yolov5 for object detection
    # then return answer to the user
    def photo_handler(self):
        @self.bot.message_handler(content_types=["photo"])
        def photo(msg):
            member = get_member_from_dynamo(name=msg.chat.id)

            # If member doesn't exist, notify is an empty dict
            notify = member.notify if member else {}

            if (
                notify[Notify.YOLO] == True
                and notify[Notify.GPT4] == False
                and notify[Notify.QUESTION] == False
            ):
                self.bot.send_message(
                    msg.chat.id, "Processing your image, kindly wait."
                )
                file_id = msg.photo[-1].file_id
                file_info = self.bot.get_file(file_id)
                photo_binary = self.bot.download_file(file_info.file_path)
                memory = BytesIO()
                memory.write(photo_binary)
                memory.seek(0)
                client = boto3.client("s3")
                path = os.path.basename(file_info.file_path)
                # try to upload picture to s3 bucket
                try:
                    client.upload_fileobj(
                        memory,
                        bucket_name,
                        f"OriginalBot/received/{path}",
                    )
                except botocore.exceptions.ClientError as e:
                    logger.info(e)
                    return False
                memory.close()
                try:
                    response = sqs_client.send_message(
                        QueueUrl=queue_url,
                        MessageBody=json.dumps(
                            {
                                "chat_id": msg.chat.id,
                                "msg_id": msg.message_id,
                                "path": f"OriginalBot/received/{os.path.basename(file_info.file_path)}",
                            }
                        ),
                    )
                    self.bot.send_message(
                        msg.chat.id, "Sent Image for processing.....")
                    logger.info(response)
                except botocore.exceptions.ClientError as e:
                    logger.error(e)
                    return False
                notify[Notify.YOLO] = False
            elif (
                notify[Notify.GPT4] == True
                and notify[Notify.YOLO] == False
                and notify[Notify] == False
            ):
                self.bot.send_message(
                    msg.chat.id,
                    "For now I can only handle messages not photos,\nif you want to detect objects in photos refer to /options .",
                )
                notify[Notify.GPT4] = False
            elif (
                notify[Notify.QUESTION] == True
                and notify[Notify.YOLO] == False
                and notify[Notify.GPT4] == False
            ):
                self.bot.send_message(
                    msg.chat.id,
                    "For now I can only handle messages not photos,\nif you want to detect objects in photos refer to /options .",
                )
                notify[Notify.QUESTION] = False
            elif notify[Notify.TEXT_TO_IMAGE] == True:
                self.bot.send_message(
                    msg.chat.id, "Its text to Image, not Image to text !!"
                )
                notify[Notify.TEXT_TO_IMAGE] = False
            else:
                self.bot.send_message(
                    msg.chat.id,
                    "It seems you tried to upload a photo, if you want to detect objects got to /options\nand choose [object detection]",
                )
            update_member_notify(name=msg.chat.id, notify_updates=notify)

    # This function responds with menu of options
    def callback(self):
        @self.bot.callback_query_handler(func=lambda call: True)
        def back(clk):
            if clk.message:
                member = get_member_from_dynamo(name=clk.message.chat.id)

                # If member doesn't exist, notify is an empty dict
                notify = member.notify if member else {}
                if clk.data == "answer_gpt4":
                    notify[Notify.GPT4] = True
                    notify[Notify.YOLO] = False
                    notify[Notify.QUESTION] = False
                    notify[Notify.TEXT_TO_IMAGE] = False

                    self.bot.send_message(
                        clk.message.chat.id,
                        "You are now chatting with GPT-4o,\nTo 'Quit' use /quit")

                    self.addReplayKeyboard(clk.message.chat.id)

                elif clk.data == "answer_yolov5":
                    notify[Notify.GPT4] = False
                    notify[Notify.YOLO] = True
                    notify[Notify.QUESTION] = False
                    notify[Notify.TEXT_TO_IMAGE] = False
                    self.bot.send_message(
                        clk.message.chat.id, "Please upload the desired photo"
                    )
                elif clk.data == "answer_question":
                    notify[Notify.GPT4] = False
                    notify[Notify.YOLO] = False
                    notify[Notify.TEXT_TO_IMAGE] = False
                    notify[Notify.QUESTION] = True
                    self.bot.send_message(
                        clk.message.chat.id, "I am listening, ask your question: "
                    )
                elif clk.data == "answer_imageToText":
                    notify[Notify.GPT4] = False
                    notify[Notify.YOLO] = False
                    notify[Notify.TEXT_TO_IMAGE] = True
                    notify[Notify.QUESTION] = False
                    self.bot.send_message(
                        clk.message.chat.id, "Enter your text to image prompt: "
                    )

                logger.error(notify)
                update_member_notify(
                    name=clk.message.chat.id, notify_updates=notify)

    # This function responds with a greeting when the user send text
    def text_handler(self):
        @self.bot.message_handler(content_types=["text"])
        async def txt(msg):
            # member = get_member_by_name(self.list_members, msg.chat.id)
            member = get_member_from_dynamo(name=msg.chat.id)

            # If member doesn't exist, notify is an empty dict
            notify = member.notify if member else {}
            logger.info(notify)
            if notify.get(Notify.GPT4):
                logger.info(f"Chat with GPT-4o Activated")
                if msg.text == "/quit":
                    notify[Notify.GPT4] = False
                    update_member_notify(
                        name=msg.chat.id, notify_updates=notify)
                    
                    self.removeReplyKeyboard(msg.chat.id)
                    return
                dynamo_obj = dynamodbAPI()
                # Get the chat log
                response = dynamo_obj.get_item(msg.chat.id)
                if "Item" not in response:
                    template = dynamo_obj.init(msg.chat.id, "user", msg.text)
                    dynamo_obj.put_item(template)

                chat_history = dynamo_obj.conver_dynamodb_dictionary_to_regular(
                    msg.chat.id
                )
                chat_history.append({"role": "user", "content": f"{msg.text}"})

                assistant_response = self.chatgpt.gpt(chat_history)

                chat_history.append(
                    {"role": "assistant", "content": f"{assistant_response}"}
                )
                self.bot.send_message(msg.chat.id, f"{assistant_response}", reply_markup=self.addReplayKeyboard(msg.chat.id))
                feed_to_dynamo_update = (
                    dynamo_obj.convert_regular_dictionary_to_dynamodb(
                        chat_history)
                )
                Item = dynamo_obj.template(msg.chat.id, feed_to_dynamo_update)
                dynamo_obj.put_item(Item)
                logger.info("Chat with GPT-4o Deactivated")
            elif notify.get(Notify.YOLO):
                self.bot.send_message(
                    msg.chat.id, "You must upload a photo not text")
            elif notify.get(Notify.QUESTION):
                logger.info("Ask a question activated")
                user_role = [{"role": "user", "content": f"{msg.text}"}]
                ans = self.chatgpt.gpt(user_role)
                self.bot.send_message(msg.chat.id, f"{ans}")
                notify[Notify.QUESTION] = False
                logger.info("Ask a question deactivated")
            elif notify.get(Notify.TEXT_TO_IMAGE):
                logger.info("Text to image activated")
                self.bot.send_message(
                    msg.chat.id, "I am on it...it might take a minute\nBe patient"
                )
                generated_url = self.chatgpt.text_to_image(msg.text)
                self.bot.send_photo(msg.chat.id, photo=generated_url)
                notify[Notify.TEXT_TO_IMAGE] = False
                logger.info("Text to image deactivated")
            else:
                self.bot.send_message(msg.chat.id, "Please refer to /options.")
            update_member_notify(name=msg.chat.id, notify_updates=notify)
