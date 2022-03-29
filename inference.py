from tendo import singleton
me = singleton.SingleInstance()
from food.tools import *
from food.paths import *
from food.psql import *

import pandas as pd
import numpy as np
from food.clipmodel import *

import os
os.environ["HF_DATASETS_OFFLINE"] = "0"
os.environ["TRANSFORMERS_OFFLINE"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
from food.tools import *
from food.psql import *
from food.paths import *
from PIL import Image
from food.clipmodel import image2clip
import custom_pandas as cpd
from tqdm import tqdm

query = """select p.id,product_name
             from foods_big p
            where p.clip is Null """

total = engine.execute(f'select count(*) from ({query}) a').one()

bs = 1
pd_iter = cpd.read_sql_query(query, engine, chunksize=bs, index_col='id')

for inp in tqdm(pd_iter, desc="clip food inference", total=total[0] // bs):  
    try:
        clip = text2clip(inp['product_name'].tolist()[0]).numpy().tolist()
        inp['clip'] = [clip]
        insert_ignore(inp,'foods_big',update=True,update_cols=['clip'],unique_cols=['id'])
    except:
        print(inp)



