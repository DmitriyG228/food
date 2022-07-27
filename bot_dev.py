#from food.psql import *
from mytools.tools import get_logger
# logger = get_logger(engine,'bot_logs','food')
# logger.debug({'msg':'starting bot'})
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

import io

import nest_asyncio
nest_asyncio.apply()

def image2file_obj(img):
    o = io.BytesIO()
    img.save(o, format=i.format)
    return o.getvalue()

async def async_search(url):
    return search(url)

async def async_image2file_obj(url):
    return image2file_obj(url)



bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)



@dp.message_handler(content_types=ContentType.PHOTO,state='*')
async def process_photo(message: types.Message, state: FSMContext):
    await message.reply('yes')
    global m 
    global i
    m = message


    photo  = message['photo'][-1]
    await photo.download(reference_images_path/photo['file_id'])
    # image_url    = await photo.get_url()
    image_url      = f'https://dima.grankin.eu/reference_images/{photo["file_id"]}'
    
    img, df,mask = await async_search(url=image_url)

    img.save('test')
    
    i = img
    
    print('started')

    img_o = await async_image2file_obj(img)
    
   
    await message.reply_doc(img_o)
    
    print('finished')

if __name__ == '__main__': executor.start_polling(dp)