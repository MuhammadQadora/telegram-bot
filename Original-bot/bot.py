import telebot
import telebot.types
from io import BytesIO
import os
from loguru import logger
import boto3, botocore.exceptions
import requests
import time 
from openAi import AI
from mongoApi import mongoAPI
token = os.environ['TELEGRAM_TOKEN']
url = os.environ['TELEGRAM_APP_URL']
bucket_name = os.environ['BUCKET_NAME']
yolo_url = os.environ['YOLO_URL']
mongo_user = os.environ['MONGO_USER']
mongo_pass = os.environ['MONGO_PASS']
database = 'gpt'
collection = 'chatlog'

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
        self.gpt4 = bool
        self.yolo = bool
        self.question = bool
        self.textToImage = bool
        self.mongo = mongoAPI(mongo_user,mongo_pass,database,collection)
    #this function continuously checks for comming messages 
    def updater(self,request):
        update = telebot.types.Update.de_json(request)
        self.bot.process_new_updates([update])
    #This function responds with a greeting when the user uses /start
    def startCommand(self):
        @self.bot.message_handler(commands=['start'])
        def start(msg):
            self.bot.send_message(msg.chat.id, f"Hi there {msg.from_user.first_name}.\nWelcome to my bot detector, to see what this Bot can do use /help .")
    #This function receives photos, uploads them to s3, posts them to Yolov5 for object detection
    #then return answer to the user
    def getHelp(self):
        @self.bot.message_handler(commands=['help'])
        def help(msg):
            self.gpt4 = False
            self.yolo = False
            self.question = False
            self.textToImage = False
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
            if self.yolo == True and self.gpt4 == False and self.question == False:
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
                self.yolo = False
            elif self.gpt4 == True and self.yolo ==False and self.question == False:
                self.bot.send_message(msg.chat.id,"For now I can only handle messages not photos,\nif you want to detect objects in photos refer to /help .")
                self.gpt4 = False
            elif self.question == True and self.yolo == False and self.gpt4 == False:
                self.bot.send_message(msg.chat.id,"For now I can only handle messages not photos,\nif you want to detect objects in photos refer to /help .")
                self.question = False
            elif self.textToImage == True:
                self.bot.send_message(msg.chat.id,"Its text to Image, not Image to text !!")
                self.textToImage = False
            else:
                self.bot.send_message(msg.chat.id,"It seems you tried to upload a photo, if you want to detect objects got to /help\nand choose object detection")


    def callback(self):
        @self.bot.callback_query_handler(func=lambda call:True)
        def back(clk):
            if clk.message:
                if clk.data == 'answer_gpt4':
                    self.gpt4 = True
                    self.yolo = False
                    self.question = False
                    self.textToImage = False
                    self.bot.send_message(clk.message.chat.id, "You are now chatting with gpt-4,to quit use /quit")
                elif clk.data == 'answer_yolov5':
                    self.gpt4 = False
                    self.yolo = True
                    self.question = False
                    self.textToImage = False
                    self.bot.send_message(clk.message.chat.id, "Please upload the desired photo")
                elif clk.data == 'answer_question':
                    self.gpt4 = False
                    self.yolo = False
                    self.textToImage = False
                    self.question = True
                    self.bot.send_message(clk.message.chat.id,"I am listening, ask your question: ")
                elif clk.data == 'answer_imageToText':
                    self.gpt4 = False
                    self.yolo = False
                    self.textToImage = True
                    self.question = False
                    self.bot.send_message(clk.message.chat.id,"Enter your text to image prompt: ")

    def text_handler(self):
        @self.bot.message_handler(content_types=['text'])
        def txt(msg):
            if self.gpt4 == True:
                logger.info(f"chat with gpt activated")
                if msg.text == '/quit':
                    self.gpt4 = False
                    return
                document_in_db = self.mongo.get_document_by_chat_id(msg.chat.id)
                if document_in_db is None:
                    self.mongo.insert_document(msg.chat.id)
                document_in_db = self.mongo.get_document_by_chat_id(msg.chat.id)
                chat_history = document_in_db['chat_history']
                chat_history.append({"role":"user","content":f"{msg.text}"})
                assistant_response = self.chatgpt.gpt(chat_history)
                chat_history.append({"role":"assistant","content":f"{assistant_response}"})
                self.bot.send_message(msg.chat.id,f"{assistant_response}")
                self.mongo.update_document_by_chat_id(msg.chat.id,chat_history)
                logger.info("chat with gpt Deactivated")
            elif self.yolo == True:
                self.bot.send_message(msg.chat.id,"You must upload a photo not Text")
            elif self.question == True:
                logger.info(f"Ask a question Activated")
                user_role = [{"role":"user","content":f"{msg.text}"}]
                ans = self.chatgpt.gpt(user_role)
                self.bot.send_message(msg.chat.id,f"{ans}")
                self.question = False
                logger.info("Ask a question Deactivated")
            elif self.textToImage == True:
                logger.info(f"Text to image Activated")
                self.bot.send_message(msg.chat.id,f"I am on it...it might take a minute\nBe patient")
                generated_url = self.chatgpt.text_to_image(msg.text)
                self.bot.send_photo(msg.chat.id,photo=generated_url)
                self.textToImage = False
                logger.info("Text to image Deactivated")
            else:
                self.bot.send_message(msg.chat.id,"Please refer to /help .")