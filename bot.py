from tendo import singleton
me = singleton.SingleInstance()

from food.psql import *
from food.tools import get_logger
logger = get_logger(engine,'bot_logs','food')
logger.debug({'msg':'starting bot'})
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ContentType
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.message import ContentTypes
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from sqlalchemy import update
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
import typing
import numpy as np


from food.paths import *


API_TOKEN = bot_token

from food.paths import *
from food.search import *
import pandas as  pd
import pytz
timezones = pytz.all_timezones
import requests
from requests.structures import CaseInsensitiveDict
import urllib
from tzwhere import tzwhere

import nest_asyncio
nest_asyncio.apply()

def geocode(q):
    geocoding_key = '5d96ac126bcb462cb373297924ab2cb4'
    url = "https://api.geoapify.com/v1/geocode/search?"

    params = {"apiKey":geocoding_key, 
              "text":q}

    resp = requests.get(url + urllib.parse.urlencode(params)).json()
    return  pd.json_normalize(resp['features']).sort_values('properties.rank.importance',ascending = False)[['properties.lat','properties.lon']].iloc[0].to_list()
   
def get_tz(q):
    lat,lon = geocode(q)
    return tzwhere.tzwhere().tzNameAt(lat,lon)
async def async_get_tz(q):
    return get_tz(q)
async def async_search_image(url, env='prod'):
    return search_image(url,env)
async def async_geocode(q):
    return geocode(q)
async def  async_insert_on_conflict(*args, **qwargs):
    return insert_on_conflict(*args, **qwargs)
async def add_sender(message):
    sender = message['from'].to_python()
    sender = pd.DataFrame(sender,index=[0]).drop(columns =['is_bot'])
    await async_insert_on_conflict(sender,'users',unique_cols=['id'])

#
def get_msg(query): 
    dish = pd.read_sql(f"""select energy,protein,carb,fat from food.dishes 
                                where user_id={query['from']['id']} and 
                                message_id = {query['message']['message_id']}
                                order by id desc limit 1""",engine)
    plot_nutients = dish[['energy','protein','carb','fat']].reset_index(drop=True)
    plot_nutients.index = ['']
    return plot_nutients.astype(int).to_string()
    
def get_today_consumed(user_id):
    today_consumed = pd.read_sql(f"""select energy,grams,timestamp from {schema}.dishes
                                    where user_id = {user_id} and timestamp > now() - interval '24 hours'
                                    and grams is not null;""",engine).set_index("timestamp")
    today_consumed= today_consumed['energy']/100*today_consumed['grams']
    user_tz = engine.execute(f"""select value from food.user_properties 
                                where user_id={user_id} and
                                property='tz'
                                order by id desc limit 1""").first()

    user_tz = user_tz[0] if user_tz else 'UTC'
    today_consumed = today_consumed.tz_convert(user_tz)
    now = pd.Timestamp.now(tz = user_tz)
    today_consumed = today_consumed.reset_index()	
    this_morning = pd.Timestamp(year = now.year,month = now.month,day = now.day,hour = 3,tz = user_tz)
    today_consumed = today_consumed[today_consumed['timestamp'] > pd.Timestamp(this_morning)][0].sum()
    return int(today_consumed),user_tz


import asyncio


bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

dishes_table = Dishes.__table__

add_dish_cb     = CallbackData('add dish', 'action')
measurment_cb   = CallbackData('measurment', 'weight')
edit_dish_cb    = CallbackData('edit_dish', 'action')
choose_metr_cb  = CallbackData('choose_metr', 'choice')

ml_version = 0.3


set_timezone_command = types.BotCommand('set_timezone','set you timezone so that we know when your day starts')
commands = [set_timezone_command]
asyncio.run(bot.set_my_commands(commands))

grams_grid  = list(np.arange(10,1000,10)[:56])
grams_grid = [str(int(v)) for v in grams_grid]
ounces_grid = list(np.arange(0.4,23,0.4)[:56])
ounces_grid = [str(round(v,1)) for v in ounces_grid]
grid_values = list(set(grams_grid+ounces_grid))
def get_keyboard(t, unit = None):
    markup = types.InlineKeyboardMarkup()
    if t == 'add dish' :  
        markup.add(types.InlineKeyboardButton('add dish', callback_data=add_dish_cb.new(action='add_dish')))
         
    elif t == 'measurment':

        btns_text = tuple(ounces_grid) if unit == 'ounces' else grams_grid


        markup = types.InlineKeyboardMarkup(row_width=8)
        
        markup.add(*(types.InlineKeyboardButton(text, callback_data=measurment_cb.new(weight=text)) for text in btns_text))

    elif t == 'edit_dish':

        btns_text = ('remove','edit weight','add again')
        markup.add(*(types.InlineKeyboardButton(text, callback_data=edit_dish_cb.new(action=text)) for text in btns_text))


    elif t == 'choose_metr':

        btns_text = ('grams','ounces')
        markup.add(*(types.InlineKeyboardButton(text, callback_data=choose_metr_cb.new(choice=text)) for text in btns_text))


    

    return markup 

async def measurment(unit, query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    logger.debug({'func':'measurment','id_key':'user_id','id_value':query['from']['id'],'msg':'measurment'})


    await query.answer()

    msg = query.to_python()['message']['text']
    msg = msg.split('\xa0')[0] if '\xa0' in msg else msg
    msg = f"{msg}\n \xa0 please choose weight of the dish in {unit}"

    await bot.edit_message_text(
        msg,
        query.from_user.id,
        query.message.message_id,
        reply_markup=get_keyboard('measurment',unit),
    )
def get_update(query,weight):
    energy = engine.execute(f"""select energy from food.dishes 
                                    where user_id={query['from']['id']}
                                    and message_id = {query['message']['message_id']}
                                    order by id desc limit 1""").first()[0]
    stmt = (
                dishes_table.update()
                            .where(dishes_table.c.message_id == query['message']['message_id'])
                            .values(grams=weight)
                            .returning(dishes_table.c.id)
        )
    session.execute(stmt)
    session.commit()

    return int(energy)

#photo recieved
@dp.message_handler(content_types=ContentType.PHOTO,state='*')
async def process_photo(message: types.Message, state: FSMContext):
    logger.debug({'func':'process_photo','id_key':'user_id','id_value':message['from']['id'],'msg':'process_photo started'})
    

    await state.finish()

    
    await types.ChatActions.typing()

    await add_sender(message)

    photo  = message['photo'][-1]
    await photo.download(reference_images_path/photo['file_id'])
    image_url = await photo.get_url()
    dish = await async_search_image(url=image_url, env='prod')
    description = dish['description'].iloc[0]


    dish['photo_id']         = photo['file_id']
    dish['photo_message_id'] = message['message_id']
    sender = message['from'].to_python()
    dish['user_id'] = sender['id']
    dish['ml_version'] = ml_version 
    dish['timestamp']=pd.Timestamp.utcnow()

    
    plot_nutients = dish[['energy','protein','carb','fat']].reset_index(drop=True)
    plot_nutients.index = ['']

    msg = f'{description}, per 100 gram \n {plot_nutients.astype(int).to_string()}'
    
    # msg = description + '\n'+ plot_nutients.astype(int).to_string()

    reply_message = await message.reply(msg, reply_markup=get_keyboard('add dish'))
    dish['message_id'] = reply_message['message_id']
    
    dish.to_sql('dishes',schema = schema,if_exists = 'append',index = False,con=engine)

    logger.debug({'func':'process_photo','id_key':'user_id','id_value':message['from']['id'],'msg':'process_photo finished'})



   
class CState(StatesGroup): 
    set_timezone    = State()
@dp.message_handler(commands=['set_timezone'])
async def set_timezone_command(message: types.Message, state: FSMContext):
    logger.debug({'func':'set_timezone_command','id_key':'user_id','id_value':message['from']['id'],'msg':'set_timezone pushed'})
    await CState.set_timezone.set()
    await message.reply(f"please search your town to set timezone")
@dp.message_handler(state=CState.set_timezone)
async def set_timezone(message: types.Message, state: FSMContext):
    logger.debug({'func':'set_timezone','id_key':'user_id','id_value':message['from']['id'],'msg':f'set_timezone to {message.text} started'})
    await types.ChatActions.typing()
    await add_sender(message)
    tz = await async_get_tz(message.text)

    df = pd.DataFrame([[message['from']['id'],'tz',tz,pd.Timestamp.utcnow()]],columns = ['user_id','property','value','timestamp'])
    df.to_sql('user_properties',schema = schema,con = engine,if_exists = 'append',index = False)

    await state.finish()

    await message.reply(f"your tz is set to {tz}")

    logger.debug({'func':'set_timezone','id_key':'user_id','id_value':message['from']['id'],'msg':f'set_timezone to {message.text} finished'})

def get_metric_unit(user_id):
    unit = engine.execute(f"""select value from food.user_properties 
                                where user_id={user_id} and
                                property='metric_unit'
                                order by id desc limit 1""").first()

    return unit[0] if unit else None

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):

    logger.debug({'func':'start_command','id_key':'user_id','id_value':message['from']['id'],'msg':'start'})
    
    await message.reply("""Counting calories as easy as taking pictures. Just capture everything before you eat it\n
                          Now send a photo of your meal to try""")
#add_dish pushed
@dp.callback_query_handler(add_dish_cb.filter(action=['add_dish']))
async def add_dish(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    logger.debug({'func':'add_dish','id_key':'user_id','id_value':query['from']['id'],'msg':'add_dish'})

    unit = get_metric_unit(query['from']['id'])
    if not unit:

        msg = query.to_python()['message']['text']
        msg = msg.split('\xa0')[0] if '\xa0' in msg else msg
        msg = f"{msg}\n \xa0 please choose unit for your food weight measurement"


        await bot.edit_message_text(
        msg,
        query.from_user.id,
        query.message.message_id,
        reply_markup=get_keyboard('choose_metr'))

    else:   
        await measurment(unit,query, callback_data)
#add_dish pushed and no metric selected
@dp.callback_query_handler(choose_metr_cb.filter(choice=['grams']))
async def select_metric_grams(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    logger.debug({'func':'select_metric_grams','id_key':'user_id','id_value':query['from']['id'],'msg':'select_metric_grams'})
    
    df = pd.DataFrame([[query['from']['id'],'metric_unit','grams',pd.Timestamp.utcnow()]],columns = ['user_id','property','value','timestamp'])
    df.to_sql('user_properties',schema = schema,con = engine,if_exists = 'append',index = False)

    await measurment('grams',query, callback_data)
#add_dish pushed and no metric selected
@dp.callback_query_handler(choose_metr_cb.filter(choice=['ounces']))
async def callback_vote_action(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    logger.debug({'func':'select_metric_ounces','id_key':'user_id','id_value':query['from']['id'],'msg':'select_metric_ounces'})

    df = pd.DataFrame([[query['from']['id'],'metric_unit','ounces',pd.Timestamp.utcnow()]],columns = ['user_id','property','value','timestamp'])
    df.to_sql('user_properties',schema = schema,con = engine,if_exists = 'append',index = False)

    await measurment('ounces',query, callback_data)
#add_dish pushed
@dp.callback_query_handler(edit_dish_cb.filter(action=['edit weight']))
async def edit_weight(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    logger.debug({'func':'edit_weight','id_key':'user_id','id_value':query['from']['id'],'msg':'edit_weight'})
    unit = get_metric_unit(query['from']['id'])
    await measurment(unit,query, callback_data)
#measure provided
@dp.callback_query_handler(measurment_cb.filter(weight=grid_values))
async def weight_processing(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):

    logger.debug({'func':'weight_processing','id_key':'user_id','id_value':query['from']['id'],'msg':'weight_processing started'})

    await query.answer()


    t = 'ounces' if 'ounces' in query.to_python()['message']['text'] else 'grams'
    u = 28.3495 if t == 'ounces' else 1

    weight = float(callback_data['weight'])

    energy = get_update(query,weight)

    msg = query.to_python()['message']['text']
    msg = msg.split('\xa0')[0] if '\xa0' in msg else msg #

    msg = f"{msg} \xa0 \n consumed {weight} {t}  \xa0 \n  {int(energy/100*u*weight)} kcall"

    today_consumed,usertz = get_today_consumed(query['from']['id'])
    msg = f"{msg}  \xa0 \n today consumed {today_consumed}"
    if usertz=='UTC': 
        msg = f"{msg}  \xa0 \n  please /set_timezone so bot knows when your day is started"
        # await bot.send_message(chat_id=query['from']['id'], 
        #                        text='please /set_timezone so bot knows when your day is started')

    

    await bot.edit_message_text(
        msg,
        query.from_user.id,
        query.message.message_id,
        reply_markup=get_keyboard('edit_dish')
    )

    logger.debug({'func':'weight_processing','id_key':'user_id','id_value':query['from']['id'],'msg':'weight_processing finished'})
    
#remove pushed
@dp.callback_query_handler(edit_dish_cb.filter(action=['remove']))
async def remove_dish(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    logger.debug({'func':'remove_dish','id_key':'user_id','id_value':query['from']['id'],'msg':'remove_dish'})
    _ = get_update(query,0)


    msg = query.to_python()['message']['text']
    msg = msg.split('\xa0')[0] if '\xa0' in msg else msg

    today_consumed,usertz = get_today_consumed(query['from']['id'])
    msg = f"{msg}  \xa0 \n today consumed {today_consumed}"
    if usertz=='UTC': 
        msg = f"{msg}  \xa0 \n  please /set_timezone so bot knows when your day is started"
        # await bot.send_message(chat_id=query['from']['id'], 
        #                        text='please /set_timezone so bot knows when your day is started')


    await query.answer()
    await bot.edit_message_text(
        msg,
        query.from_user.id,
        query.message.message_id,
        reply_markup=get_keyboard('add dish'))
#add again pushed
@dp.callback_query_handler(edit_dish_cb.filter(action=['add again']))
async def add_again(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    logger.debug({'func':'add_again','id_key':'user_id','id_value':query['from']['id'],'msg':'add_again'})


    dish = pd.read_sql(f"""select description,energy,protein,carb,fat,score,photo_id,user_id,ml_version,photo_message_id
                from food.dishes 
                                                    where user_id={query['from']['id']}
                                                    and message_id = {query['message']['message_id']} limit 1""",engine)
    dish['timestamp'] = pd.Timestamp.utcnow()


    msg = query.to_python()['message']['text']
    msg = msg.split('\xa0')[0] if '\xa0' in msg else msg

    today_consumed,usertz = get_today_consumed(query['from']['id'])
    msg = f"{msg}  \xa0 \n today consumed {today_consumed}"
    if usertz=='UTC': 
        msg = f"{msg}  \xa0 \n  please /set_timezone so bot knows when your day is started"


        # await bot.send_message(chat_id=query['from']['id'], 
        #                        text='please /set_timezone so bot knows when your day is started')



    await query.answer()
    message = await bot.send_message(chat_id=query['from']['id'], 
                                     reply_to_message_id = dish['photo_message_id'].iloc[0],
                                     text=msg, 
                                     reply_markup=get_keyboard('add dish'))

    dish['message_id'] = message['message_id']
    dish.to_sql('dishes',schema = schema,if_exists = 'append',index = False,con=engine)
    
    

if __name__ == '__main__':
    executor.start_polling(dp)