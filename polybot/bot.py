import os
import requests
import time
import telebot
from io import BytesIO
from loguru import logger
import telebot.types
import boto3, botocore.exceptions

TELEGRAM_APP_URL = os.environ['TELEGRAM_APP_URL']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
IMAGES_BUCKET = os.environ['BUCKET_NAME']
YOLO_URL = os.environ['YOLO_URL']

class Util:

    def __init__(self, json_data):
        self.json_data = json_data

    def objects_counter(self):
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
            result = f'👀👇🏼 𝔻𝕖𝕥𝕖𝕔𝕥𝕖𝕕 𝕆𝕓𝕛𝕖𝕔𝕥𝕤 👇🏼👀\n'
            for key, val in class_count.items():
                result += f"\t{key}\t👉🏼\t{val}\n"
            return result


class Bot:
    # Initiate connection with telegram
    def __init__(self):
        self.bot = telebot.TeleBot(token=TELEGRAM_TOKEN)
        self.bot.remove_webhook()
        time.sleep(1)
        self.bot.set_webhook(url=f"{TELEGRAM_APP_URL}/{TELEGRAM_TOKEN}", timeout=60)
        logger.info(f"Connected to bot:\n{self.bot.get_me()}")

    # this function continuously checks for comming messages
    def updater(self, request):
        update = telebot.types.Update.de_json(request)
        self.bot.process_new_updates([update])

    # This function responds with a greeting when the user uses /start
    def startCommand(self):
        @self.bot.message_handler(commands=['start'])
        def start(msg):
            self.bot.send_message(msg.chat.id,f"☣️ 𝕎𝕖𝕝𝕔𝕠𝕞𝕖 𝕋𝕠 𝔹𝕒𝕥𝕞𝕒𝕟 𝔹𝕠𝕥 ☣️\nℍ𝕖𝕝𝕝𝕠, {msg.from_user.first_name} 👋🏻\nℍ𝕠𝕨 𝕔𝕒𝕟 𝕀 𝕙𝕖𝕝𝕡 𝕪𝕠𝕦?\n/help")

    # This function responds with a greeting when the user uses /help
    def getHelp(self):
        @self.bot.message_handler(commands=['help'])
        def help(msg):
            self.bot.send_message(msg.chat.id,
                                    f"ℂ𝕦𝕣𝕣𝕖𝕟𝕥𝕝𝕪 𝕥𝕙𝕚𝕤 𝕓𝕠𝕥 𝕚𝕤 𝕔𝕒𝕡𝕒𝕓𝕝𝕖 𝕠𝕗 𝕣𝕖𝕔𝕖𝕚𝕧𝕚𝕟𝕘 𝕒 𝕡𝕚𝕔𝕥𝕦𝕣𝕖 𝕒𝕟𝕕 𝕚𝕕𝕖𝕟𝕥𝕚𝕗𝕪𝕚𝕟𝕘 𝕠𝕓𝕛𝕖𝕔𝕥𝕤.\n𝕊𝕠𝕠𝕟 𝕨𝕚𝕝𝕝 𝕓𝕖 𝕔𝕒𝕡𝕒𝕓𝕝𝕖 𝕠𝕗 𝕙𝕒𝕟𝕕𝕝𝕚𝕟𝕘 𝕧𝕚𝕕𝕖𝕠𝕤 𝕒𝕟𝕕 𝕨𝕚𝕝𝕝 𝕒𝕝𝕝𝕠𝕨 𝔾ℙ𝕋-𝟜 𝕔𝕠𝕞𝕞𝕦𝕟𝕚𝕔𝕒𝕥𝕚𝕠𝕟.")

    # This function responds with a greeting when the user uses /version
    def getVersion(self):
        @self.bot.message_handler(commands=['version'])
        def version(msg):
            self.bot.send_message(msg.chat.id, f"✅ 𝔹𝕒𝕥𝕞𝕒𝕟 𝔹𝕠𝕥 𝕍𝕖𝕣𝕤𝕚𝕠𝕟 𝟙.𝟘.𝟘 ✅")

    # This function receives photos, uploads them to s3, posts them to Yolov5 for object detection
    # then return answer to the user
    def downloadPhoto(self):
        @self.bot.message_handler(content_types=['photo'])
        def photo(msg):
            self.bot.send_message(msg.chat.id, f"ℙ𝕝𝕖𝕒𝕤𝕖 𝕎𝕒𝕚𝕥..😶‍🌫️𝕀'𝕞 𝕎𝕠𝕣𝕜𝕚𝕟𝕘 𝕆𝕟 𝕀𝕥😶‍🌫️")
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
                processed_data = utility.objects_counter()
                self.bot.reply_to(msg, f"{processed_data}")
            else:
                self.bot.send_message(
                    msg.chat.id, f"⛔️𝕊𝕠𝕞𝕖𝕥𝕙𝕚𝕟𝕘 𝕨𝕖𝕟𝕥 𝕨𝕣𝕠𝕟𝕘, 𝕖𝕚𝕥𝕙𝕖𝕣 𝕥𝕙𝕖 𝕚𝕞𝕒𝕘𝕖 𝕔𝕠𝕟𝕥𝕒𝕚𝕟𝕤 𝕟𝕠 𝕠𝕓𝕛𝕖𝕔𝕥\n𝕠𝕣 𝕥𝕙𝕖 𝕚𝕞𝕒𝕘𝕖 𝕤𝕚𝕫𝕖 𝕚𝕤 𝕥𝕠𝕠 𝕓𝕚𝕘\n𝕡𝕝𝕖𝕒𝕤𝕖 𝕥𝕣𝕪 𝕒𝕘𝕒𝕚𝕟⛔️!")
    




# class ObjectDetectionBot(Bot):
#     def handle_message(self, msg):
#         logger.info(f'Incoming message: {msg}\n')

#         match msg:
#             case _ if ObjectDetectionBot.is_current_msg_type(msg, 'photo'):
#                 self.send_text(msg['chat']['id'],
#                                f"ℙ𝕝𝕖𝕒𝕤𝕖 𝕎𝕒𝕚𝕥..😶‍🌫️𝕀'𝕞 𝕎𝕠𝕣𝕜𝕚𝕟𝕘 𝕆𝕟 𝕀𝕥😶‍🌫️")
#                 # TODO download the user photo (utilize download_user_photo)
#                 file_path = self.download_user_photo(msg)

#                 # TODO upload the photo to S3
#                 client = boto3.client('s3')
#                 try:
#                     client.upload_file(file_path, IMAGES_BUCKET,
#                                        f"bot/received/{os.path.basename(file_path)}")
#                     logger.info(f"Uploaded {os.path.basename(file_path)}\n")
#                     print("uploaded")
#                 except ClientError as e:
#                     logger.info(f'{e}\n')
#                     return False
#                 try:
#                     # TODO send a request to the `yolo5` service for prediction localhost:8081/predict?imgName=nfb
#                     response = requests.post(
#                         f"{URL_YOLO}/predict?imgName=bot/received/{os.path.basename(file_path)}")

#                     # TODO send results to the Telegram end-user
#                     if response.ok:
#                         self.send_text(msg['chat']['id'], f"🫡 𝔸𝕝𝕞𝕠𝕤𝕥 𝔻𝕠𝕟𝕖 🫡")
#                         data = response.json()
#                         utility = Util(data)
#                         processed_data = utility.objects_counter()
#                         self.send_text(msg['chat']['id'], f"🫣 ℍ𝕖𝕣𝕖 𝕎𝕙𝕒𝕥 𝔸
#                                         𝔾𝕠𝕥 🫣\n{processed_data}")
#                     elif response.status_code == 404:
#                         self.send_text(
#                             msg['chat']['id'], f"⛔️ 𝕊𝕠𝕣𝕣𝕪 ⛔️\n𝕀 ℂ𝕒𝕟'𝕥 𝔽𝕠𝕦𝕟𝕕 𝔸𝕟𝕪 𝕆𝕓𝕛𝕖𝕔𝕥,\n𝕋𝕣𝕪 𝔸𝕟𝕠𝕥𝕙𝕖𝕣 ℙ𝕙𝕠𝕥𝕠")
#                     else:
#                         raise Exception(response.status_code)
#                 except ConnectionError as e:
#                     self.send_text(msg['chat']['id'],
#                                    f"⛔️ 𝕊𝕠𝕞𝕖𝕥𝕙𝕚𝕟𝕘 𝕎𝕖𝕟𝕥 𝕎𝕣𝕠𝕟𝕘 ⛔️")
#                     logger.info(f'{e}\n')
#                     return False

#             case _ if ObjectDetectionBot.is_current_msg_type(msg, 'text'):
#                 # TODO handle text messages
#                 text = msg["text"]

#                 if (text.startswith('/start')):
#                     self.send_text(msg['chat']['id'], f"☣️ 𝕎𝕖𝕝𝕔𝕠𝕞𝕖 𝕋𝕠 𝔹𝕒𝕥𝕞𝕒𝕟 
#                                     𝔹𝕠𝕥 ☣️\nℍ𝕖𝕝𝕝𝕠, {msg['from']['first_name']} 👋🏻\nℍ𝕠𝕨 𝕔𝕒𝕟 𝕀 𝕙𝕖𝕝𝕡 𝕪𝕠𝕦?")
#                 elif (text.startswith('/help')):
#                     self.send_text(msg['chat']['id'],
#                                    f"⛔️ ℕ𝕠𝕥 𝔸𝕧𝕒𝕚𝕝𝕒𝕓𝕝𝕖 𝔽𝕠𝕣 𝕋𝕙𝕚𝕤 𝔹𝕠𝕥 ⛔️")
#                 elif (text.startswith('/version')):
#                     self.send_text(msg['chat']['id'],
#                                    f"✅ 𝔹𝕒𝕥𝕞𝕒𝕟 𝔹𝕠𝕥 𝕍𝕖𝕣𝕤𝕚𝕠𝕟 𝟙.𝟘.𝟘 ✅")
#                 elif (text.startswith('/chatgpt')):
#                     self.send_text(msg['chat']['id'],
#                                    f"🔞🔜 ℂ𝕙𝕒𝕥 𝕎𝕚𝕥𝕙 ℂ𝕙𝕒𝕥𝔾ℙ𝕋 🔜🔞")
#                 else:
#                     self.send_text(
#                         msg['chat']['id'], f"𝕐𝕠𝕦 𝕊𝕖𝕟𝕥 𝔸 𝕋𝕖𝕩𝕥 𝕄𝕖𝕤𝕤𝕒𝕘𝕖:\n{msg['text']}")
#             case _:
#                 # TODO handle other types of messages
#                 self.send_text(
#                     msg['chat']['id'], "😵‍💫 𝕊𝕠𝕣𝕣𝕪, 𝕀 ℂ𝕒𝕟 𝕆𝕟𝕝𝕪 ℍ𝕒𝕟𝕕𝕝𝕖 'ℙ𝕙𝕠𝕥𝕠𝕤' 𝔸𝕟𝕕 '𝕋𝕖𝕩𝕥𝕤' 😵‍💫")