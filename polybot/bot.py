import os
import requests
import time
import telebot
from openai import OpenAI
from io import BytesIO
from loguru import logger
from telebot import types
import boto3
import botocore.exceptions

TELEGRAM_APP_URL = os.environ['TELEGRAM_APP_URL']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
IMAGES_BUCKET = os.environ['BUCKET_NAME']
YOLO_URL = os.environ['YOLO_URL']
GPT_KEY = os.environ['GPT_KEY']

isPhoto = bool
sentPhoto = bool
isGPT = bool
chatWithGPT = bool
textToIMG = bool
client = OpenAI(api_key=GPT_KEY)


class Util:

    def __init__(self, json_data):
        self.json_data = json_data

    def SendMessageForGPT(self, msg):
        try:
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
                    {"role": "user", "content": f"{msg.text}"}
                ]
            )
            if completion.choices:
                self.bot.send_message(
                    msg.chat.id, completion.choices[0].message.content)
            else:
                self.bot.send_message(msg.chat.id, "ERROR WITH GPT")
        except Exception as e:
            logger.info("Error:", e)

    def ObjectsCounter(self):
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
            return "🤕🤧😷\tZero objects Detected\t🤕🤧😷"
        else:
            result = f"🫣ℍ𝕖𝕣𝕖 𝕎𝕙𝕒𝕥 𝕀 𝔾𝕠𝕥🫣\n👀👇🏼 𝔻𝕖𝕥𝕖𝕔𝕥𝕖𝕕 𝕆𝕓𝕛𝕖𝕔𝕥𝕤 👇🏼👀\n"
            for key, val in class_count.items():
                result += f"\t{key}\t👉🏼\t{val}\n"
            return result

    def GenerateIMG(self, msg):
        self.bot.send_message(msg.chat.id, f"🥸ℂ𝕣𝕖𝕒𝕥𝕚𝕟𝕘 𝕒𝕟 𝕚𝕞𝕒𝕘𝕖 𝕗𝕠𝕣 𝕪𝕠𝕦🥸\n😮‍💨𝕁𝕦𝕤𝕥 𝕙𝕠𝕝𝕕 𝕠𝕟 𝕒 𝕞𝕠𝕞𝕖𝕟𝕥😮‍💨")
        try:
            response = client.images.generate(
            model="dall-e-3",
            prompt=msg.text,
            size="1024x1024",
            quality="standard",
            n=1,
            )
            image_url = response.data[0].url
            self.bot.reply_to(msg, image_url)
        except:
            print("\n\n\nAn unexpected error occurred while trying")


class Bot:
    # Initiate connection with telegram
    def __init__(self):
        self.bot = telebot.TeleBot(token=TELEGRAM_TOKEN)
        self.bot.remove_webhook()
        time.sleep(1)
        self.bot.set_webhook(
            url=f"{TELEGRAM_APP_URL}/{TELEGRAM_TOKEN}", timeout=60)
        logger.info(f"Connected to bot:\n{self.bot.get_me()}")
        self.isPhoto = False
        self.sentPhoto = False
        self.isGPT = False
        self.chatWithGPT = False
        self.textToIMG = False

    # this function continuously checks for comming messages
    def updater(self, request):
        update = telebot.types.Update.de_json(request)
        self.bot.process_new_updates([update])

    # This function responds with a greeting when the user uses /start
    def startCommand(self):
        @self.bot.message_handler(commands=['start'])
        def start(msg):
            self.bot.send_message(msg.chat.id, f"☣️ 𝕎𝕖𝕝𝕔𝕠𝕞𝕖 𝕋𝕠 𝔹𝕒𝕥𝕞𝕒𝕟 𝔹𝕠𝕥 ☣️\nℍ𝕖𝕝𝕝𝕠, {msg.from_user.first_name} 👋🏻\nℍ𝕠𝕨 𝕔𝕒𝕟 𝕀 𝕙𝕖𝕝𝕡 𝕪𝕠𝕦?")

    # This function responds with a greeting when the user uses /help
    def getHelp(self):
        @self.bot.message_handler(commands=['help'])
        def help(msg):
            self.isGPT = False
            self.isPhoto = False
            self.sentPhoto = False
            self.chatWithGPT = False
            self.textToIMG = False
            # self.bot.send_message(
            #     msg.chat.id, f"ℂ𝕦𝕣𝕣𝕖𝕟𝕥𝕝𝕪 𝕥𝕙𝕚𝕤 𝕓𝕠𝕥 𝕚𝕤 𝕔𝕒𝕡𝕒𝕓𝕝𝕖 𝕠𝕗 𝕣𝕖𝕔𝕖𝕚𝕧𝕚𝕟𝕘 𝕒 𝕡𝕚𝕔𝕥𝕦𝕣𝕖 𝕒𝕟𝕕 𝕚𝕕𝕖𝕟𝕥𝕚𝕗𝕪𝕚𝕟𝕘 𝕠𝕓𝕛𝕖𝕔𝕥𝕤.\n𝕊𝕠𝕠𝕟 𝕨𝕚𝕝𝕝 𝕓𝕖 𝕔𝕒𝕡𝕒𝕓𝕝𝕖 𝕠𝕗 𝕙𝕒𝕟𝕕𝕝𝕚𝕟𝕘 𝕧𝕚𝕕𝕖𝕠𝕤 𝕒𝕟𝕕 𝕨𝕚𝕝𝕝 𝕒𝕝𝕝𝕠𝕨 𝔾ℙ𝕋-𝟜 𝕔𝕠𝕞𝕞𝕦𝕟𝕚𝕔𝕒𝕥𝕚𝕠𝕟.")

            # Creating an inline keyboard with two buttons
            markup = types.InlineKeyboardMarkup()
            markup.row_width = 2
            button1 = types.InlineKeyboardButton(
                '🦇𝕀𝕕𝕖𝕟𝕥𝕚𝕗𝕪 𝕆𝕓𝕛𝕖𝕔𝕥𝕤🦇', callback_data='idnObj')
            button2 = types.InlineKeyboardButton(
                '🤠𝔸𝕤𝕜 𝔸 ℚ𝕦𝕖𝕤𝕥𝕚𝕠𝕟🤠', callback_data='gptQuest')
            button3 = types.InlineKeyboardButton(
                '🤖ℂ𝕙𝕒𝕥 𝕎𝕚𝕥𝕙 𝔾ℙ𝕋🤖', callback_data='gptChat')
            button4 = types.InlineKeyboardButton(
                '👽𝔾𝕖𝕟𝕖𝕣𝕒𝕥𝕖 ℙ𝕙𝕠𝕥𝕠👽', callback_data='genPic')
            markup.add(button1, button2, button3, button4)

            # Sending a message with the inline keyboard
            self.bot.send_message(
                msg.chat.id, "🧐ℂ𝕙𝕠𝕠𝕤𝕖 𝕒𝕟 𝕠𝕡𝕥𝕚𝕠𝕟:🧐", reply_markup=markup)

    # This function responds with a greeting when the user uses /help - Options
    def getOpions(self):
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            if call.data == 'idnObj':
                self.isPhoto = True
                self.isGPT = False
                self.chatWithGPT = False
                self.textToIMG = False
                self.bot.send_message(
                    call.message.chat.id, "🫣ℙ𝕝𝕖𝕒𝕤𝕖 𝕤𝕖𝕟𝕕 𝕒 𝕡𝕙𝕠𝕥𝕠🫣")
            elif call.data == 'gptQuest':
                self.isGPT = True
                self.chatWithGPT = False
                self.isPhoto = False
                self.textToIMG = False
                self.bot.send_message(
                    call.message.chat.id, "👂𝕎𝕙𝕒𝕥 𝕪𝕠𝕦 𝕨𝕚𝕤𝕙 𝕥𝕠 𝕣𝕖𝕢𝕦𝕖𝕤𝕥👂")
            elif call.data == 'gptChat':
                self.isGPT = True
                self.chatWithGPT = True
                self.isPhoto = False
                self.textToIMG = False
                self.bot.send_message(
                    call.message.chat.id, f"ℕ𝕠𝕨 𝕪𝕠𝕦 𝕦𝕤𝕖𝕤 𝕒 ℂ𝕙𝕒𝕥 𝕎𝕚𝕥𝕙 𝔾ℙ𝕋-𝟜 𝕄𝕠𝕕𝕖\n𝕋𝕠 𝕖𝕟𝕕 𝕚𝕥 𝕡𝕝𝕖𝕒𝕤𝕖 𝕤𝕖𝕟𝕕 /closegpt")
            elif call.data == 'genPic':
                self.textToIMG = True
                self.isGPT = False
                self.chatWithGPT = False
                self.isPhoto = False
                self.bot.send_message(
                    call.message.chat.id, f"🧐𝔾𝕚𝕧𝕖 𝕞𝕖 𝕒 𝕕𝕖𝕤𝕔𝕣𝕚𝕡𝕥𝕚𝕠𝕟 𝕠𝕗 𝕥𝕙𝕖 𝕡𝕙𝕠𝕥𝕠🧐")

    # This function responds with a greeting when the user uses /version
    def getVersion(self):
        @self.bot.message_handler(commands=['version'])
        def version(msg):
            self.bot.send_message(msg.chat.id, f"✅ 𝔹𝕒𝕥𝕞𝕒𝕟 𝔹𝕠𝕥 𝕍𝕖𝕣𝕤𝕚𝕠𝕟 𝟙.𝟘.𝟘 ✅")

    # This function responds with a greeting when the user uses /closegpt
    def getCloseGPT(self):
        @self.bot.message_handler(commands=['closegpt'])
        def text(msg):
            self.chatWithGPT = False
            self.isGPT = False
            self.bot.send_message(msg.chat.id, f"👻🦇🤖🦇👻")

    # This function receives photos, uploads them to s3, posts them to Yolov5 for object detection
    # then return answer to the user
    def getPhoto(self):
        @self.bot.message_handler(content_types=['photo'])
        def photo(msg):
            self.sentPhoto = True
            if (self.isPhoto == True and self.sentPhoto == True):
                self.bot.send_message(
                    msg.chat.id, f"ℙ𝕝𝕖𝕒𝕤𝕖 𝕎𝕒𝕚𝕥..😶‍🌫️𝕀'𝕞 𝕎𝕠𝕣𝕜𝕚𝕟𝕘 𝕆𝕟 𝕀𝕥😶‍🌫️")
                file_id = msg.photo[-1].file_id
                file_info = self.bot.get_file(file_id)
                photo_binary = self.bot.download_file(file_info.file_path)
                memory = BytesIO()
                memory.write(photo_binary)
                memory.seek(0)
                client = boto3.client('s3')
                # try to upload picture to s3 bucket
                try:
                    client.upload_fileobj(
                        memory, IMAGES_BUCKET, f"Bot/received/{os.path.basename(file_info.file_path)}")
                except botocore.exceptions.ClientError as e:
                    logger.info(e)
                    return False
                memory.close()
                # try posting to predict endpoint /predict
                self.bot.send_message(msg.chat.id, f"🫡 𝔸𝕝𝕞𝕠𝕤𝕥 𝔻𝕠𝕟𝕖 🫡")
                try:
                    response = requests.post(url=f"{
                        YOLO_URL}/predict?imgName=Bot/received/{os.path.basename(file_info.file_path)}")
                except requests.exceptions.RequestException as e:
                    self.bot.send_message(
                        msg.chat.id, f"⛔️𝕀𝕥 𝕤𝕖𝕖𝕞𝕤 𝕥𝕙𝕒𝕥 𝕥𝕙𝕖 𝕤𝕖𝕣𝕧𝕖𝕣 𝕚𝕤 𝕟𝕠𝕥 𝕨𝕠𝕣𝕜𝕚𝕟𝕘 𝕡𝕣𝕠𝕡𝕖𝕣𝕝𝕪⛔️")
                    logger.info(e)
                if response.status_code == 200:
                    data = response.json()
                    utility = Util(data)
                    processed_data = utility.ObjectsCounter()
                    self.bot.reply_to(msg, f"{processed_data}")
                else:
                    self.bot.send_message(
                        msg.chat.id, f"⛔️𝕊𝕠𝕞𝕖𝕥𝕙𝕚𝕟𝕘 𝕨𝕖𝕟𝕥 𝕨𝕣𝕠𝕟𝕘, 𝕖𝕚𝕥𝕙𝕖𝕣 𝕥𝕙𝕖 𝕚𝕞𝕒𝕘𝕖 𝕔𝕠𝕟𝕥𝕒𝕚𝕟𝕤 𝕟𝕠 𝕠𝕓𝕛𝕖𝕔𝕥\n𝕠𝕣 𝕥𝕙𝕖 𝕚𝕞𝕒𝕘𝕖 𝕤𝕚𝕫𝕖 𝕚𝕤 𝕥𝕠𝕠 𝕓𝕚𝕘\n𝕡𝕝𝕖𝕒𝕤𝕖 𝕥𝕣𝕪 𝕒𝕘𝕒𝕚𝕟⛔️!")
                self.isPhoto = False
            else:
                self.bot.send_message(
                    msg.chat.id, f"👻𝕐𝕠𝕦 𝕞𝕒𝕪 𝕦𝕤𝕖 /help 𝕥𝕠 𝕤𝕖𝕖 𝕞𝕪 𝕥𝕒𝕝𝕖𝕟𝕥𝕤👻")

    # This function receives videos
    def getVideo(self):
        @self.bot.message_handler(content_types=['video'])
        def video(msg):
            self.bot.send_message(
                msg.chat.id, "😵‍💫 𝕊𝕠𝕣𝕣𝕪, 𝕀 ℂ𝕒𝕟 𝕆𝕟𝕝𝕪 ℍ𝕒𝕟𝕕𝕝𝕖 'ℙ𝕙𝕠𝕥𝕠𝕤' 𝔸𝕟𝕕 '𝕋𝕖𝕩𝕥𝕤' 😵‍💫")

    # This function responds with a message when the user sends a text message that contains
    def getText(self):
        @self.bot.message_handler(content_types=['text'])
        def text(msg):
            if self.isGPT:
                if not self.chatWithGPT:
                    self.bot.send_message(
                    msg.chat.id, f"👾𝕁𝕦𝕤𝕥 𝕒 𝕞𝕠𝕞𝕖𝕟𝕥, 𝕀'𝕞 𝕠𝕟 𝕚𝕥👾")
                    Util.SendMessageForGPT(self, msg)
                    self.isGPT = False
                    self.isPhoto = False
                    self.sentPhoto = False
                else:
                    Util.SendMessageForGPT(self, msg)
            elif self.isPhoto  and not self.sentPhoto:
                self.bot.send_message(msg.chat.id, "🫣ℙ𝕝𝕖𝕒𝕤𝕖 𝕤𝕖𝕟𝕕 𝕒 𝕡𝕙𝕠𝕥𝕠🫣")
            elif self.textToIMG:
                Util.GenerateIMG(self, msg)
                self.textToIMG = False
            else:
                self.bot.send_message(
                    msg.chat.id, f"𝕐𝕠𝕦 𝕊𝕖𝕟𝕥 𝔸 𝕋𝕖𝕩𝕥 𝕄𝕖𝕤𝕤𝕒𝕘𝕖:\n{msg.text}\n👻𝕐𝕠𝕦 𝕞𝕒𝕪 𝕦𝕤𝕖 /help 𝕥𝕠 𝕤𝕖𝕖 𝕞𝕪 𝕥𝕒𝕝𝕖𝕟𝕥𝕤👻")
