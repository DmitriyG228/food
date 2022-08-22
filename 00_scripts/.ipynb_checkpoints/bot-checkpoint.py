import sys
sys.path.insert(0,'..')
from food.psql import *
from mytools.tools import get_logger
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
import io


from food.paths import *


API_TOKEN = bot_token

from food.paths import *
import pandas as  pd
import pytz
timezones = pytz.all_timezones
import requests
from requests.structures import CaseInsensitiveDict
import urllib
from tzwhere import tzwhere


from segmentor.segment import get_segment_model
from food.search import *
from mytools.psql import *

async def  async_insert_on_conflict(*args, **qwargs):
    return insert_on_conflict(*args, **qwargs)
async def add_sender(message):
    logger.debug({'func':'add_sender','id_key':'user_id','id_value':message['from']['id'],'msg':'add_sender'})
    sender = message['from'].to_python()
    sender = pd.DataFrame(sender,index=[0]).drop(columns =['is_bot'])
    await async_insert_on_conflict(sender,'users',unique_cols=['id'],engine = engine)
def plot_nutrition(masks):
    attributes = ['energy','protein','carb','fat']
    nutrition ={}
    for m,a in zip(masks,attributes): nutrition[a] = float(m[m!=0].mean())
    return pd.DataFrame(nutrition,index = ['']).fillna(0).astype(int).to_string()
def image2file_obj(img):
    o = io.BytesIO()
    f = img.format if img.format else 'jpeg'
    img.save(o, format=f)
    return o.getvalue()
async def async_image2file_obj(*args,**kwargs):
    return image2file_obj(*args,**kwargs)

async def async_search(*args,**kwargs):
    return search(*args,**kwargs)

async def async_visualize_array(*args,**kwargs):
    return visualize_array(*args,**kwargs)



model_path = checkpoints_path.ls()[0]
segment_model = get_segment_model(model_path)


bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dishes_table = Dishes.__table__


add_dish_cb     = CallbackData('add to food log', 'action')
remove_cb       = CallbackData('remove from food log', 'action')


def attribute_score(cals,values,scores):
    arrays = []
    for n in range(len(values)-1):
        arrays.append(np.stack([np.linspace(values[n],values[n+1]),np.flip(np.linspace(scores[n+1],scores[n]))]))
        formula = np.concatenate(arrays,axis=1)
        c = formula[0][formula[0] <cals][-1]

    return formula[1][formula[0]==c].astype(np.int32)[0]
def get_food_score(cals,protein):
    return attribute_score(cals   ,calore_scores[0],calore_scores[1]),attribute_score(protein,protein_scores[0],protein_scores[1])
protein_scores = ([0,10,20,35],
                  [30,90,100,100])
calore_scores  = ([0,  90, 100,150,200,300,400],
                  [100,100, 95,70 ,60 ,50 ,30])
text = ':thumbs_down:'
#emoji.emojize(text)
def get_keyboard(t, unit = None):
    markup = types.InlineKeyboardMarkup()
    if t == 'add to food log' :  
        # btns_text = ['add to food log',':thumbs_up:',':thumbs_down:']
        markup.add(types.InlineKeyboardButton('add to food log', callback_data=add_dish_cb.new(action='add_dish')))
        # markup.add(*(types.InlineKeyboardButton('add to food log', callback_data=remove_cb.new(action=text)) for text in btns_text))
         

    elif t == 'remove from food log':

        btns_text = ('remove from food log',)
        markup.add(types.InlineKeyboardButton('remove from food log', callback_data=remove_cb.new(action='remove')))
        
        
        # markup.add(*(types.InlineKeyboardButton(text, callback_data=remove_cb.new(action=text)) for text in btns_text))

    return markup 
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    global m 
    m = message
    logger.debug({'func':'start_command','id_key':'user_id','id_value':message['from']['id'],'msg':'start_command'})
    await add_sender(message)

    await message.reply(""" Take <b>food pictures</b> to improve your diet.\n 

No  more calorie counting, food weight measurement, manual food logging. <b>A single picture per dish is the only thing you need to do</b> .\n
Your photos are returned back to you colorised as a heat map. Just choose more of coloured in green  next time and less of colorer in  red.\n
Get your <b>nutrition score</b> updated with every meal, try to keep it high.\n
<b>Calorie density</b> is a scientific approach that allows to <b>eat till satisfaction while still cutting back on calories</b>. That idea is implemented <b>with the power of AI</b> to be as easy to follow as taking pictures.\n


<b>how it gain great results:</b>\n
- eat only till sutisfaction and do not overeat.
- try not to drink your calories.
- take photos of all the foods <b>from the same distance</b> and with the same focus distance each time\n
- <b>use flash</b>\n

Now <b>take a picture of your next dish</b> with the bot!""",parse_mode = 'HTML')
# Take <b>pictures of your food</b> to know how healthy it is with the power of <b>AI</b>.\n\
    
#     Get your <b>nutrition score</b> updated every time you take a meal.\n \
#     Keep high food score to stay fit and healthy.\n<b>Take a picture of your next dish with the bot!</b>
@dp.message_handler(content_types=ContentType.PHOTO,state='*')
async def process_photo(message: types.Message, state: FSMContext):
    logger.debug({'func':'process_photo','id_key':'user_id','id_value':message['from']['id'],'msg':'process_photo started'})
    
    processing_reply = await message.reply("""\xa0 your picture is being processed ...""",
                           parse_mode = 'HTML')
    
    await types.ChatActions.upload_photo()
    photo  = message['photo'][-1]
    path = reference_images_path/photo['file_id']
    await photo.download(path)
    
    # image_url    = await photo.get_url()
    image_url      = f'https://dima.grankin.eu/reference_images/{photo["file_id"]}'
    
    img,clip_df,masks,stats = await async_search(segment_model,path,prompt_factor=0.1,min_score=0.22,exand_times =2)
    
    print('after search')

    dish = clip_df.reset_index()[['id','score','area']]
    dish['photo_id']         = photo['file_id']
    dish['photo_message_id'] = message['message_id']
    sender = message['from'].to_python()
    dish['user_id'] = sender['id']
    dish['ml_version'] = 0.4 
    dish['timestamp']=pd.Timestamp.utcnow()
    dish = dish.rename(columns = {"id":'food_id'})
    
    output = '; '.join(clip_df['description'].tolist())

    print('downloaded')

    img_o = await async_image2file_obj(img)
    
    await processing_reply.delete()
    reply = await message.reply_photo(img_o,caption=f'<i>per 100 gram</i>:\n{plot_nutrition(masks)} \n\n{output}', reply_markup=get_keyboard('add to food log'),parse_mode = 'HTML')
    dish['message_id'] = reply['message_id']
    
    dish.to_sql('dishes',con=engine,if_exists='append',index = False,schema = 'food')
    
    logger.debug({'func':'process_photo','id_key':'user_id','id_value':message['from']['id'],'msg':'process_photo finished'})
    
    
async def get_today_consumed(user_id):

    today_consumed = pd.read_sql( f"""select f.energy, f.protein, d.area,d.timestamp
                           from food.foods f
                           join food.dishes d on (f.id = d.food_id)
                           where d.user_id = {user_id} and 
                                 d.timestamp > now() - interval '24 hours' and
                                 d.added is true""" ,engine).set_index("timestamp")

    
    area = today_consumed['area'].sum()
    if area>0:
        cals = np.average(today_consumed['energy'] ,weights=today_consumed['area'])
        prts = np.average(today_consumed['protein'],weights=today_consumed['area'])
        cals_score, prts_score =  get_food_score(cals,prts)
        food_score = int((cals_score*2+prts_score)/3)


        return int(food_score),int(cals),int(cals_score),int(prts_score),int(prts),area
    
    else: return None,None,None,None,None,0
async def add_remove(query,add):
    
    msg = query.to_python()['message']['caption']
    msg = msg.split('\xa0')[0] if '\xa0' in msg else msg
    
    stmt = (
        dishes_table.update()
                    .where(dishes_table.c.message_id == query['message']['message_id'])
                    .values(added=add)
                    .returning(dishes_table.c.id)
        )
    session.execute(stmt)
    session.commit()
    
    user_id = query['from']['id']
    
    food_score,cals,cals_score,prts,prts_score,area = await get_today_consumed(user_id)
    
    if cals_score < 70:
        if prts_score <70:
            m = 'Keep choosing foods in a <b>greener</b> spectrum and have a bit of <b>protein</b> rich foods'
        else:
            m = 'Keep choosing foods in a <b>greener</b> spectrum'
    else:
        if prts_score <70:
            m = 'Your calories are good. Try to have more of <b>protein</b> rich foods to improve your nutrition score'
        else:
            m = 'you are doing <b>great</b>!'


    
    if add:
        if area>300000: 
            msg = f"{msg}\n\n\xa0your <b>nutrition score</b> for the last 24 hours is <b>{food_score}</b>"
            msg = f"{msg}\n\n\xa0<i>{m}</i>"
        else:
            msg = f"{msg}\n\n\xa0keep adding your dishes to get your food score"
            
        
    keyboard = 'remove from food log' if add else 'add to food log' 

    await bot.edit_message_caption(query.from_user.id,
                                    query.message.message_id,
                                    caption = msg,
                                    reply_markup=get_keyboard(keyboard),
                                    parse_mode = 'HTML')
    
#add_dish pushed
@dp.callback_query_handler(add_dish_cb.filter(action=['add_dish']))
async def add_dish(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    logger.debug({'func':'add_dish','id_key':'user_id','id_value':query['from']['id'],'msg':'add_dish'})
    
    await add_remove(query,True)
#remove_dish pushed
@dp.callback_query_handler(remove_cb.filter(action=['remove']))
async def remove_dish(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    logger.debug({'func':'remove_dish','id_key':'user_id','id_value':query['from']['id'],'msg':'remove_dish'})
    
    await add_remove(query,False)
if __name__ == '__main__': executor.start_polling(dp)