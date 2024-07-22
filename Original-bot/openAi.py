import os
from openai import OpenAI
import openai
from loguru import logger
from io import BytesIO
import requests
from sec import secret_keys

openai_key = secret_keys["openai_key"]


class AI:
    def __init__(self):
        self.client = OpenAI(api_key=openai_key)

    def gpt(self, user_message):
        try:
            response = self.client.chat.completions.create(
                messages=user_message, model="gpt-4o"
            )
            assistant_response = response.choices[0].message.content
            return assistant_response
        except openai.OpenAIError as e:
            logger.info(e)

    def text_to_image(self, user_message):
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=f"{user_message}",
                size="1024x1024",
                quality="hd",
                n=1,
            )

            image_url = response.data[0].url
            image_data = requests.get(image_url).content
            return image_data
        except openai.OpenAIError as e:
            logger.info(e)
