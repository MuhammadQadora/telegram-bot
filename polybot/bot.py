import os
import boto3
import requests
import telebot
import time
from loguru import logger
from telebot.types import InputFile
from botocore.exceptions import ClientError

URL_YOLO = os.environ['YOLO_URL']
IMAGES_BUCKET = os.environ['BUCKET_NAME']


class Bot:

    def __init__(self, token, telegram_chat_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(
            url=f'{telegram_chat_url}/{token}/', timeout=60)

        logger.info(
            f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}\n')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(
            chat_id, text, reply_to_message_id=quoted_msg_id)

    @staticmethod
    def is_current_msg_type(msg, type):
        return type in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_type(msg, 'photo'):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(
            msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}\n')
        self.send_text(msg['chat']['id'],
                        f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}\n')

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(
                msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])


class ObjectDetectionBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}\n')

        match msg:
            case _ if ObjectDetectionBot.is_current_msg_type(msg, 'photo'):
                self.send_text(msg['chat']['id'], f"ℙ𝕝𝕖𝕒𝕤𝕖 𝕎𝕒𝕚𝕥..😶‍🌫️𝕀'𝕞 𝕎𝕠𝕣𝕜𝕚𝕟𝕘 𝕆𝕟 𝕀𝕥😶‍🌫️")
                # TODO download the user photo (utilize download_user_photo)
                file_path = self.download_user_photo(msg)

                # TODO upload the photo to S3
                client = boto3.client('s3')
                try:
                    client.upload_file(file_path, IMAGES_BUCKET,
                                        f"bot/received/{os.path.basename(file_path)}")
                    logger.info(f"Uploaded {os.path.basename(file_path)}\n")
                    print("uploaded")
                except ClientError as e:
                    logger.info(f'{e}\n')
                    return False
                try:
                    # TODO send a request to the `yolo5` service for prediction localhost:8081/predict?imgName=nfb
                    response = requests.post(
                        f"{URL_YOLO}/predict?imgName=bot/received/{os.path.basename(file_path)}")
                    
                    # TODO send results to the Telegram end-user
                    if response.ok:
                        self.send_text(msg['chat']['id'], f"🫡 𝔸𝕝𝕞𝕠𝕤𝕥 𝔻𝕠𝕟𝕖 🫡")
                        data = response.json()
                        utility = Util(data)
                        processed_data = utility.objects_counter()
                        self.send_text(msg['chat']['id'], f"🫣 ℍ𝕖𝕣𝕖 𝕎𝕙𝕒𝕥 𝔸 𝔾𝕠𝕥 🫣\n{processed_data}")
                    elif response.status_code == 404:
                        self.send_text(msg['chat']['id'], f"⛔️ 𝕊𝕠𝕣𝕣𝕪 ⛔️\n𝕀 ℂ𝕒𝕟'𝕥 𝔽𝕠𝕦𝕟𝕕 𝔸𝕟𝕪 𝕆𝕓𝕛𝕖𝕔𝕥,\n𝕋𝕣𝕪 𝔸𝕟𝕠𝕥𝕙𝕖𝕣 ℙ𝕙𝕠𝕥𝕠")
                    else:
                        raise Exception(response.status_code)
                except ConnectionError as e:
                    self.send_text(msg['chat']['id'], f"⛔️ 𝕊𝕠𝕞𝕖𝕥𝕙𝕚𝕟𝕘 𝕎𝕖𝕟𝕥 𝕎𝕣𝕠𝕟𝕘 ⛔️")
                    logger.info(f'{e}\n')
                    return False
            
            case _ if ObjectDetectionBot.is_current_msg_type(msg, 'text'):
                # TODO handle text messages
                text = msg["text"]
                
                if(text.startswith('/start')): 
                    self.send_text(msg['chat']['id'], f"☣️ 𝕎𝕖𝕝𝕔𝕠𝕞𝕖 𝕋𝕠 𝔹𝕒𝕥𝕞𝕒𝕟 𝔹𝕠𝕥 ☣️\nℍ𝕖𝕝𝕝𝕠, {msg['from']['first_name']} 👋🏻\nℍ𝕠𝕨 𝕔𝕒𝕟 𝕀 𝕙𝕖𝕝𝕡 𝕪𝕠𝕦?")
                elif(text.startswith('/help')):
                    self.send_text(msg['chat']['id'], f"⛔️ ℕ𝕠𝕥 𝔸𝕧𝕒𝕚𝕝𝕒𝕓𝕝𝕖 𝔽𝕠𝕣 𝕋𝕙𝕚𝕤 𝔹𝕠𝕥 ⛔️")
                elif(text.startswith('/version')):
                    self.send_text(msg['chat']['id'], f"✅ 𝔹𝕒𝕥𝕞𝕒𝕟 𝔹𝕠𝕥 𝕍𝕖𝕣𝕤𝕚𝕠𝕟 𝟙.𝟘.𝟘 ✅")
                elif(text.startswith('/chatgpt')):
                    self.send_text(msg['chat']['id'], f"🔞🔜 ℂ𝕙𝕒𝕥 𝕎𝕚𝕥𝕙 ℂ𝕙𝕒𝕥𝔾ℙ𝕋 🔜🔞")
                else:
                    self.send_text(msg['chat']['id'], f"𝕐𝕠𝕦 𝕊𝕖𝕟𝕥 𝔸 𝕋𝕖𝕩𝕥 𝕄𝕖𝕤𝕤𝕒𝕘𝕖:\n{msg["text"]}")
            case _:
                # TODO handle other types of messages
                self.send_text(msg['chat']['id'], "😵‍💫 𝕊𝕠𝕣𝕣𝕪, 𝕀 ℂ𝕒𝕟 𝕆𝕟𝕝𝕪 ℍ𝕒𝕟𝕕𝕝𝕖 'ℙ𝕙𝕠𝕥𝕠𝕤' 𝔸𝕟𝕕 '𝕋𝕖𝕩𝕥𝕤' 😵‍💫")


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
