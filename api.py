# cd; conda activate re; cd re_foto; uvicorn api:app --port 8181

from tendo import singleton
me = singleton.SingleInstance()

import pandas as pd
from food.tools import *
from food.psql import *
from food.paths import *
from food.milvus import *
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from food.clip import *

# _,country_dict = from_pickle('location_dicts.pkl')



app = FastAPI(title="airbnb search by natural text", version="0.2",)
app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.post("/search/")
async def search(text:str,
           topk:int=48,
        #    country      :str=None,
           min_bedrooms :int=None,
           min_beds     :int=None,
           min_price    :float=None,
           max_price    :float=None,
           min_latitude :float=None,
           max_latitude :float=None,
           min_longitude:float=None,
           max_longitude:float=None):
    params = {k:v for k,v in locals().items() if v!=None}
    # if 'country' in params.keys(): 
    #     params['country_id'] = country_dict[country]  
    params.pop('text',None)
    params.pop('topk',None)
    # params.pop('country',None)
    return search_by_text(text, topk, params).to_json()