# from tendo import singleton
# me = singleton.SingleInstance()
from food.tools import *
from food.paths import *
from food.psql import *

import pandas as pd
import numpy as np
from food.clipmodel import *

import os
os.environ["HF_DATASETS_OFFLINE"] = "2"
os.environ["TRANSFORMERS_OFFLINE"] = "2"
os.environ["CUDA_VISIBLE_DEVICES"] = "2"
from food.tools import *
from food.psql import *
from food.paths import *
from PIL import Image
from food.clipmodel import image2clip
import custom_pandas as cpd
from tqdm import tqdm

query = """select id,product_name,keywords,ingredients_text,categories,food_groups
             from foods_big
            where clip is Null """

total = engine.execute(f'select count(*) from ({query}) a').one()

bs = 1
pd_iter = cpd.read_sql_query(query, engine, chunksize=bs, index_col='id')

for inp in tqdm(pd_iter, desc="clip food inference", total=total[0] // bs):  
    try:
        text =inp.fillna("")
        for c in text.columns: text[c] = text[c].str.replace('NaN','')
        text = text['product_name']+ '. ' + text['food_groups']#+ '. '+ text['categories']+ '. ' + text['ingredients_text']+'. ' + text['keywords'] 
        clip = text2clip(text.tolist()[0][:150]).numpy().tolist()
        inp['clip'] = [clip]
        insert_ignore(inp,'foods_big',update=True,update_cols=['clip'],unique_cols=['product_name'])
    except RuntimeError as e:
        print(e)





