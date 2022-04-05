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

import datetime
import pytz
from tzwhere import tzwhere

def get_tz_offset(lat,lon):
    timezone_str = tzwhere.tzwhere().tzNameAt(lat,lon)

    timezone = pytz.timezone(timezone_str)
    dt = datetime.datetime.utcnow()
    return timezone.utcoffset(dt).total_seconds()/60/60

token = "5091011572:AAG4NfkC_zZjcsaAFkwLm4ZXOvhEqyLpQhY"

m = None

bot = telebot.TeleBot(token)
bot.dish = None


@bot.message_handler(commands=['start'])
def send_welcome(message):
	markup = types.ReplyKeyboardMarkup()
	markup.add('/help')
	bot.reply_to(message, "Counting calories as easy as taking pictures. Just capture everything before you eat it", reply_markup=markup)
	bot.reply_to(message, "Now send a photo of your meal to try", reply_markup=markup)
	bot.reply_to(message, "PLease send your location to adjust your timezone", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def send_welcome(message):
	bot.send_chat_action(message.chat.id, 'typing')
	tz = tzwhere.tzwhere().tzNameAt(message.location.latitude, message.location.longitude)

	df = pd.DataFrame([[message.from_user.id,
              message.location.latitude,
              message.location.longitude,
              tz]],
              columns = ['id','lat','lon','timezone'])

	insert_ignore(df,'users',update = True, update_cols = ['lat','lon','timezone'], engine = engine,unique_cols=['id'])

	bot.reply_to(message, f"your timezone is set to {tz}")



@bot.message_handler(commands=['help'])
def send_welcome(message):
	bot.reply_to(message, "join our support group https://t.me/+nIBkPkw3vpM0NDJi")

@bot.message_handler(commands=['cancel'])
def send_cancel(message):
	markup = types.ReplyKeyboardRemove(selective=False)
	bot.reply_to(message, f"", reply_markup=markup)


@bot.message_handler(content_types=['photo'])
def calssify_image(message):

	bot.send_chat_action(message.chat.id, 'typing')
	
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

	cancel = types.KeyboardButton('/cancel')
	[markup.add(p) for p in bot.measures['portion_description'].tolist()]
	markup.add(cancel)

	bot.send_message(message.chat.id, "Choose amount:", reply_markup=markup)


	




@bot.message_handler(regexp="[0-9]+")
def handle_grams(message):

	if hasattr(bot,'dish'):  
		grams = bot.measures[bot.measures['portion_description'] == message.text]['gram_weight'].iloc[0]
		bot.dish[['energy','protein','carb','fat']]/100*grams
		bot.dish['grams']=grams
		bot.dish['measure_selected'] = message.text
		bot.dish = bot.dish.rename(columns = {'id':'food_id'})
		bot.dish['timestamp']=pd.Timestamp.utcnow()

		bot.dish.to_sql('dishes',engine,if_exists='append',index=False)

	
		markup = types.ReplyKeyboardRemove(selective=False)
		
		
		

		today_consumed = pd.read_sql(f"select energy,timestamp from dishes where user_id = {message.from_user.id} and timestamp > now() - interval '24 hours';",engine).set_index("timestamp")
		user_tz = engine.execute(f'select timezone from users where id={message.from_user.id}').first()
		if user_tz: today_consumed = today_consumed.tz_convert(user_tz[0])
		today_consumed = today_consumed.reset_index()	
		today_consumed = today_consumed[today_consumed['timestamp'].dt.time > datetime.time(3,0)]['energy'].sum()



		bot.reply_to(message, f"you have consumed {today_consumed} kcall today", reply_markup=markup)

bot.infinity_polling()
