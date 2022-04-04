from tendo import singleton
me = singleton.SingleInstance()


from food.tools import *
from food.paths import *

import pandas as pd
import numpy as np
import requests
import telebot
from food.psql import *

# !nbdev_build_lib
from food.classify_image import *

from telebot import types

token = "5091011572:AAG4NfkC_zZjcsaAFkwLm4ZXOvhEqyLpQhY"

m = None

bot = telebot.TeleBot(token)
bot.dish = None


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Howdy, how are you doing?")




@bot.message_handler(content_types=['photo'])
def calssify_image(message):

	bot.send_chat_action(message.chat.id, 'typing') #does not seem to work
	global m
	m = message
	image_url = bot.get_file_url(message.photo[3].file_id)
	bot.dish = search_image(url=image_url)
	bot.dish['image_url'] = image_url
	bot.dish['user_id']= message.from_user.id

	plot_numtients = bot.dish[['energy','protein','carb','fat']].reset_index(drop=True)
	plot_numtients.index = ['']

	bot.reply_to(message, bot.dish['description'].iloc[0])
	bot.reply_to(message, plot_numtients.to_string())

	bot.measures = pd.read_sql(f"select portion_description,gram_weight from portions where food_id = {bot.dish['id'].iloc[0]}",engine)

	markup = types.ReplyKeyboardMarkup(row_width=2)

	cancel = types.KeyboardButton('cancel')
	[markup.add(p) for p in bot.measures['portion_description'].tolist()]
	markup.add(cancel)

	bot.send_message(message.chat.id, "Choose amount:", reply_markup=markup)


@bot.message_handler(regexp="[0-9]+")
def handle_grams(message):
	global m
	m = message
	if hasattr(bot,'dish'):  
		grams = bot.measures[bot.measures['portion_description'] == message.text]['gram_weight'].iloc[0]
		bot.dish[['energy','protein','carb','fat']]/100*grams
		bot.dish['grams']=grams
		bot.dish['measure_selected'] = message.text
		bot.dish = bot.dish.rename(columns = {'id':'food_id'})
		bot.dish['timestamp']=pd.Timestamp.utcnow() #should be user local time


		bot.reply_to(message, bot.dish)
		bot.dish.to_sql('dishes',engine,if_exists='append',index=False)

		last_day = pd.read_sql(f"select sum(energy) from dishes where user_id = {message.from_user.id} and timestamp > now() - interval '24 hours';",engine)

		markup = types.ReplyKeyboardRemove(selective=False)
		bot.reply_to(message, f"you have consumed {last_day.iloc[0]['sum']} kcall in the last 24 hours", reply_markup=markup)

bot.infinity_polling()

