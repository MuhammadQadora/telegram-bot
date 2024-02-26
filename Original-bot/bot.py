import telebot
import telebot.types
from io import BytesIO
import os
from loguru import logger
import boto3, botocore.exceptions
import requests
import time


token = os.environ['TELEGRAM_TOKEN']
url = os.environ['TELEGRAM_APP_URL']
bucket_name = os.environ['BUCKET_NAME']
yolo_url = os.environ['YOLO_URL']


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
    #this function continuously checks for comming messages 
    def updater(self,request):
        update = telebot.types.Update.de_json(request)
        self.bot.process_new_updates([update])
    #This function responds with a greeting when the user uses /start
    def startCommand(self):
        @self.bot.message_handler(commands=['start'])
        def start(msg):
            self.bot.send_message(msg.chat.id, f"Hi there {msg.from_user.first_name}.\nWelcome to my bot detector")
    #This function receives photos, uploads them to s3, posts them to Yolov5 for object detection
    #then return answer to the user
    def getHelp(self):
        @self.bot.message_handler(commands=['help'])
        def help(msg):
            self.bot.send_message(msg.chat.id,
                                  "Currently this bot is capable of receiving a picture and identifying objects.\nSoon will be capable of handling videos and will allow GPT-4 communication.")
    def downloadPhoto(self):
        @self.bot.message_handler(content_types=['photo'])
        def photo(msg):
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
            #try posting to predict endpoint /predict
            self.bot.send_message(msg.chat.id,"Almost Done..")
            try:
                response = requests.post(url=f"{yolo_url}/predict?imgName=OriginalBot/received/{os.path.basename(file_info.file_path)}")
            except requests.exceptions.RequestException as e:
                self.bot.send_message(msg.chat.id, "It seems that the server is not working properly!")
                logger.info(e)
            if response.status_code == 200:
                data = response.json()
                utility = Util(data)
                processed_data = utility.object_count()
                self.bot.reply_to(msg, f"{processed_data}")
            else:
                self.bot.send_message(msg.chat.id,"Something went wrong, either the image contains no object\nor the image size is too big\nplease try again!")