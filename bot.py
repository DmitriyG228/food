from tendo import singleton
me = singleton.SingleInstance()


from food.tools import *
from food.paths import *

import pandas as pd
import numpy as np
import requests
import telebot

from food.classify_image import *
token = "5091011572:AAG4NfkC_zZjcsaAFkwLm4ZXOvhEqyLpQhY"

bot = telebot.TeleBot(token)
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Hi, send photos of your food here")
@bot.message_handler(content_types=['photo'])
def echo_all(message):
	file_info = bot.get_file(message.photo[3].file_id)
	responce = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(token, file_info.file_path))

	file = open('photo', "wb")
	file.write(responce.content)
	file.close()

	df = search_image(path = 'photo')
	bot.reply_to(message, df['name'].loc[0])



bot.infinity_polling()