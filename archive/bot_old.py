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
from food.search import *

from telebot import types

import datetime
import pytz
from tzwhere import tzwhere


debug = False

dishes = 'dishes_test'  if debug else 'dishes'
users = 'users_test'    if debug else 'users'

token = "5091011572:AAG4NfkC_zZjcsaAFkwLm4ZXOvhEqyLpQhY" if debug else '5203882708:AAG3G_Y2oZSr-rMG2zoffDVtj3d0KkOFSts'



m = None

bot = telebot.TeleBot(token)
bot.dish = None


@bot.message_handler(commands=['start'])
def welcome(message):
	bot.message = message
	markup = types.ReplyKeyboardMarkup(row_width=1,resize_keyboard=True)
	markup.add('/help')
	bot.reply_to(message, "Counting calories as easy as taking pictures. Just capture everything before you eat it", reply_markup=markup)
	bot.reply_to(message, "Now send a photo of your meal to try", reply_markup=markup)


@bot.message_handler(commands=['show_last_items'])
def show_last(message):
	bot.message = message

	markup = types.ReplyKeyboardMarkup(row_width=1,resize_keyboard=True)
	markup.add('/help')
	bot.reply_to(message, "Counting calories as easy as taking pictures. Just capture everything before you eat it", reply_markup=markup)
	bot.reply_to(message, "Now send a photo of your meal to try", reply_markup=markup)






@bot.message_handler(content_types=['location'])
def location(message):
	bot.message = message

	bot.send_chat_action(message.chat.id, 'typing')
	tz = tzwhere.tzwhere().tzNameAt(message.location.latitude, message.location.longitude)

	df = pd.DataFrame([[message.from_user.id,
              message.location.latitude,
              message.location.longitude,
              tz]],
              columns = ['id','lat','lon','timezone'])

	insert_on_conflict(df,f'food.{users}',update = True, update_cols = ['lat','lon','timezone'], engine = engine,unique_cols=['id'])
	bot.reply_to(message, f"your timezone is set to {tz}")



@bot.message_handler(commands=['help'])
def help(message):
	bot.message = message
	bot.reply_to(message, "join our community group https://t.me/+nIBkPkw3vpM0NDJi")

@bot.message_handler(commands=['cancel'])
def send_cancel(message):
	bot.message = message
	markup = types.ReplyKeyboardRemove(selective=False)
	bot.reply_to(message, f"cancalled", reply_markup=markup)
	if hasattr(bot,'dish'): del bot.dish
	if hasattr(bot,'measures'): del bot.measures
	if hasattr(bot,'measurement'): del bot.measurement
	if hasattr(bot,'label'): del bot.label

@bot.message_handler(content_types=['photo'])
def calssify_image(message):
	bot.message = message

	bot.send_chat_action(message.chat.id, 'typing')
	
	image_url = bot.get_file_url(message.photo[3].file_id)
	to_pickle(image_url,'image_url')
	bot.dish = search_image(url=image_url)
	bot.dish['image_url'] = image_url
	bot.dish['user_id']= message.from_user.id

	plot_numtients = bot.dish[['energy','protein','carb','fat']].reset_index(drop=True)
	plot_numtients.index = ['']


	bot.label = bot.dish['description'].iloc[0]

	bot.reply_to(message, bot.label)
	bot.reply_to(message, plot_numtients.to_string())

	bot.measures = pd.read_sql(f"select portion_description,gram_weight from food.portions where food_id = {bot.dish['id'].iloc[0]}",engine)
	
	bot.measures['portion_description'] = bot.measures['portion_description']+' ('+bot.measures['gram_weight'].astype('int').astype('str')+' grams)'

	bot.measures_cleaned = bot.measures['portion_description'].str.replace('1 ','').tolist()+['gram']

	markup = types.ReplyKeyboardMarkup(row_width=2)
	cancel = types.KeyboardButton('/cancel')
	[markup.add(p) for p in bot.measures_cleaned]
	markup.add(cancel)

	bot.send_message(message.chat.id, "Choose the unit to measure the weight of you dish", reply_markup=markup)


@bot.message_handler(content_types=['text']) #regexp="[0-9]+"
def handle_text(message):
	bot.message = message
	try:     bot.number = float(message.text)
	except:  bot.number = None

	if not bot.number and hasattr(bot,'label'):
		

		if len(set(bot.measures_cleaned) & set([message.text])) >0:
			bot.measurement = message.text
			markup = types.ReplyKeyboardMarkup(row_width=2)
			if bot.measurement == 'gram': [markup.add(str(p)) for p in range(10,400,10)]
			else:[markup.add(str(p)) for p in [0.5,1,1.5,2,3,4,5,6,7,8,9,10]]
			cancel = types.KeyboardButton('/cancel')
			markup.add(cancel)
			bot.reply_to(message, f"select number of {bot.measurement}s you are going to eat", reply_markup=markup)

		else:
			bot.reply_to(message, f"please choose a unit from the list")



	

	elif bot.number and hasattr(bot,'label'): 
		if bot.measurement == 'gram': grams = bot.number
		else:grams = bot.measures[bot.measures['portion_description'].str.contains(bot.measurement, regex=False)]['gram_weight'].iloc[0]*bot.number
		bot.dish[['energy','protein','carb','fat']] = bot.dish[['energy','protein','carb','fat']]/100*grams
		bot.dish['grams']=grams
		bot.dish['measure_selected'] = message.text
		bot.dish = bot.dish.rename(columns = {'id':'food_id'})
		bot.dish['timestamp']=pd.Timestamp.utcnow()
		bot.dish = bot.dish[['food_id', 'description', 'category', 'energy', 'protein', 'carb',
								'fat', 'score', 'image_url', 'user_id', 'grams', 'measure_selected',
								'timestamp']]

		bot.dish.to_sql(dishes,engine,if_exists='append',index=False,schema = 'food')

	
		markup = types.ReplyKeyboardRemove(selective=False)

		today_consumed = pd.read_sql(f"select energy,timestamp from food.{dishes} where user_id = {message.from_user.id} and timestamp > now() - interval '24 hours';",engine).set_index("timestamp")
		user_tz = engine.execute(f'select timezone from food.{users} where id={message.from_user.id}').first()
		user_tz = user_tz[0] if user_tz else 'UTC'
		today_consumed = today_consumed.tz_convert(user_tz)
		if user_tz == 'UTC': bot.reply_to(message, "Please send your location to that we know your local time", reply_markup=markup)
		now = pd.Timestamp.now(tz = user_tz)
		today_consumed = today_consumed.reset_index()	
		this_morning = pd.Timestamp(year = now.year,month = now.month,day = now.day,hour = 3,tz = user_tz)
		today_consumed = today_consumed[today_consumed['timestamp'] > pd.Timestamp(this_morning)]['energy'].sum()


		bot.reply_to(message, f" {bot.number} {bot.measurement}s  of {bot.label} added", reply_markup=markup)
		bot.reply_to(message, f"You have consumed {round(today_consumed)} kcall today", reply_markup=markup)

		del bot.dish
		del bot.measures
		del bot.measurement
		del bot.label

	elif not hasattr(bot,'label'):

		bot.reply_to(message, f"Please take a photo of your dish")




	

bot.infinity_polling()