import telebot
import telebot.types
from io import BytesIO
import os
from loguru import logger
import boto3, botocore.exceptions
import requests
import time 
from openAi import AI
from sec import secret_keys
import json
from dynamodbAPI import dynamodbAPI
from local_user_DB import *

list_members = []

##################
token = secret_keys['TELEGRAM_TOKEN']
url = secret_keys['TELEGRAM_APP_URL']
bucket_name = secret_keys['BUCKET_NAME']
queue_url = secret_keys['SQS_URL']
region_name = secret_keys['REGION_NAME']
sns_topic_arn = secret_keys['SNS_ARN']
table = secret_keys['DYNAMO_TBL']
server_endpoint = secret_keys['SERVER_ENDPOINT']
#######################

sqs_client = boto3.client('sqs',region_name=region_name)

########################
class Util:
    def __init__(self, json_data):
        self.json_data = json_data
    def object_count(self):
        total_items = len(self.json_data['labels'])
        print(f"There are {total_items} items in the JSON")
        class_count = {}
        for item in self.json_data['labels']:
            class_name = item["class"]
            if class_name in class_count:
                class_count[class_name] += 1
            else:
                class_count[class_name] = 1
        if len(class_count) == 0:
            return "Zero objects Detected :("
        else:
            result = 'Detected Objects:\n'
            for key,val in class_count.items():
                result += f"{key}: {val}\n"
            return result

class Bot:
    #Initiate connection with telegram
    def __init__(self):
        self.bot = telebot.TeleBot(token=token)
        self.bot.remove_webhook()
        time.sleep(1)
        self.bot.set_webhook(f"{url}/{token}",timeout=60)
        logger.info(f"Connected to bot:\n{self.bot.get_me()}")
        self.chatgpt = AI()

    #this function continuously checks for comming messages 
    def updater(self,request):
        update = telebot.types.Update.de_json(request)
        self.bot.process_new_updates([update])
    #This function responds with a greeting when the user uses /start
    def startCommand(self):
        @self.bot.message_handler(commands=['start'])
        def start(msg):
            global list_members
            logger.info(list_members)
            self.bot.send_message(msg.chat.id, f"Hi there {msg.from_user.first_name}.\nWelcome to my bot detector, to see what this Bot can do use /help .")
            add_member(list_members, msg.chat.id)
            logger.info(len(list_members))

    #This function receives photos, uploads them to s3, posts them to Yolov5 for object detection
    #then return answer to the user
    def getHelp(self):
        @self.bot.message_handler(commands=['help'])
        def help(msg):
            global list_members
            
            if is_member_in_list_by_name(list_members, msg.chat.id):
                member = get_member_by_name(list_members, msg.chat.id)
                notify = member.notify
                # Setting all notifications to False
                for notification in Notify:
                    notify[notification] = False
            else:
                add_member(list_members, msg.chat.id)
            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            gpt_4 = telebot.types.InlineKeyboardButton('Chat with gpt-4', callback_data='answer_gpt4')
            yolov5 = telebot.types.InlineKeyboardButton('Object Detection',callback_data='answer_yolov5')
            text_to_image = telebot.types.InlineKeyboardButton('Text to Image',callback_data='answer_imageToText')
            gpt_one_question = telebot.types.InlineKeyboardButton('Ask a question',callback_data='answer_question')
            markup.add(gpt_4,yolov5,gpt_one_question,text_to_image)
            self.bot.send_message(msg.chat.id,"Available Options",reply_markup=markup)

    def photo_handler(self):
        @self.bot.message_handler(content_types=['photo'])
        def photo(msg):
            global list_members
            
            n = get_notify_by_member_name(list_members,msg.chat.id)
            if n[Notify.YOLO] == True and n[Notify.GPT4]==False and n[Notify.QUESTION]==False:
                self.bot.send_message(msg.chat.id,"Processing your image, kindly wait.")
                file_id = msg.photo[-1].file_id
                file_info = self.bot.get_file(file_id)
                photo_binary= self.bot.download_file(file_info.file_path)
                memory = BytesIO()
                memory.write(photo_binary)
                memory.seek(0)
                client = boto3.client('s3')
                #try to upload picture to s3 bucket
                try:
                    client.upload_fileobj(memory, bucket_name, f"OriginalBot/received/{os.path.basename(file_info.file_path)}")
                except botocore.exceptions.ClientError as e:    
                    logger.info(e)
                    return False
                memory.close()
                try:
                    response = sqs_client.send_message(
                        QueueUrl=queue_url,
                        MessageBody=json.dumps({"chat_id": msg.chat.id,"msg_id": msg.message_id ,"path": f"OriginalBot/received/{os.path.basename(file_info.file_path)}"})
                        )
                    self.bot.send_message(msg.chat.id,"Sent Image for processing.....")
                    logger.info(response)
                except botocore.exceptions.ClientError as e:
                    logger.error(e)
                    return False
                n[Notify.YOLO] = False
            elif n[Notify.GPT4] == True and n[Notify.YOLO] == False and n[Notify] == False:
                self.bot.send_message(msg.chat.id,"For now I can only handle messages not photos,\nif you want to detect objects in photos refer to /help .")
                n[Notify.GPT4] = False
            elif n[Notify.QUESTION] == True and n[Notify.YOLO] == False and n[Notify.GPT4] == False :
                self.bot.send_message(msg.chat.id,"For now I can only handle messages not photos,\nif you want to detect objects in photos refer to /help .")
                n[Notify.QUESTION] = False
            elif n[Notify.TEXT_TO_IMAGE] == True:
                self.bot.send_message(msg.chat.id,"Its text to Image, not Image to text !!")
                n[Notify.TEXT_TO_IMAGE] = False
            else:
                self.bot.send_message(msg.chat.id,"It seems you tried to upload a photo, if you want to detect objects got to /help\nand choose object detection")


    def callback(self):
        @self.bot.callback_query_handler(func=lambda call:True)
        def back(clk):
            if clk.message:
                member = get_member_by_name(list_members, clk.message.chat.id)
                notify = member.notify if member else {}  # If member doesn't exist, notify is an empty dict
                if clk.data == 'answer_gpt4':
                    notify[Notify.GPT4] = True
                    notify[Notify.YOLO] = False
                    notify[Notify.QUESTION] = False
                    notify[Notify.TEXT_TO_IMAGE] = False
                    self.bot.send_message(clk.message.chat.id, "You are now chatting with gpt-4,to quit use /quit")
                elif clk.data == 'answer_yolov5':
                    notify[Notify.GPT4] = False
                    notify[Notify.YOLO] = True
                    notify[Notify.QUESTION] = False
                    notify[Notify.TEXT_TO_IMAGE] = False
                    self.bot.send_message(clk.message.chat.id, "Please upload the desired photo")
                elif clk.data == 'answer_question':
                    notify[Notify.GPT4] = False
                    notify[Notify.YOLO] = False
                    notify[Notify.TEXT_TO_IMAGE] = False
                    notify[Notify.QUESTION] = True
                    self.bot.send_message(clk.message.chat.id,"I am listening, ask your question: ")
                elif clk.data == 'answer_imageToText':
                    notify[Notify.GPT4] = False
                    notify[Notify.YOLO] = False
                    notify[Notify.TEXT_TO_IMAGE] = True
                    notify[Notify.QUESTION] = False
                    self.bot.send_message(clk.message.chat.id,"Enter your text to image prompt: ")

    def text_handler(self):
        @self.bot.message_handler(content_types=['text'])
        def txt(msg):
            member = get_member_by_name(list_members, msg.chat.id)
            notify = member.notify if member else {}  # If member doesn't exist, notify is an empty dict

            if notify.get(Notify.GPT4):
                logger.info(f"Chat with GPT-4 activated")
                if msg.text == '/quit':
                    notify[Notify.GPT4] = False
                    return
                dynamo_obj = dynamodbAPI()
                # Get the chat log
                response = dynamo_obj.get_item(msg.chat.id)
                if 'Item' not in response:
                    template = dynamo_obj.init(msg.chat.id, 'user', msg.text)
                    dynamo_obj.put_item(template)

                chat_history = dynamo_obj.conver_dynamodb_dictionary_to_regular(msg.chat.id)
                chat_history.append({"role": "user", "content": f"{msg.text}"})

                assistant_response = self.chatgpt.gpt(chat_history)

                chat_history.append({"role": "assistant", "content": f"{assistant_response}"})
                self.bot.send_message(msg.chat.id, f"{assistant_response}")
                feed_to_dynamo_update = dynamo_obj.convert_regular_dictionary_to_dynamodb(chat_history)
                Item = dynamo_obj.template(msg.chat.id, feed_to_dynamo_update)
                dynamo_obj.put_item(Item)
                logger.info("Chat with GPT-4 Deactivated")
            elif notify.get(Notify.YOLO):
                self.bot.send_message(msg.chat.id, "You must upload a photo not text")
            elif notify.get(Notify.QUESTION):
                logger.info("Ask a question activated")
                user_role = [{"role": "user", "content": f"{msg.text}"}]
                ans = self.chatgpt.gpt(user_role)
                self.bot.send_message(msg.chat.id, f"{ans}")
                notify[Notify.QUESTION] = False
                logger.info("Ask a question deactivated")
            elif notify.get(Notify.TEXT_TO_IMAGE):
                logger.info("Text to image activated")
                self.bot.send_message(msg.chat.id, "I am on it...it might take a minute\nBe patient")
                generated_url = self.chatgpt.text_to_image(msg.text)
                self.bot.send_photo(msg.chat.id, photo=generated_url)
                notify[Notify.TEXT_TO_IMAGE] = False
                logger.info("Text to image deactivated")
            else:
                self.bot.send_message(msg.chat.id, "Please refer to /help.")