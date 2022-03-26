from tendo import singleton
me = singleton.SingleInstance()
from food.milvus import collection
from time import sleep
from food.tools import from_pickle
from food.psql import *
import pandas as pd
from tqdm import tqdm
import custom_pandas as cpd
query = f"""select    f.*
            FROM      foods    f
            LEFT JOIN indexed  i  ON (i.id =       f.id)
            WHERE f .clip    is not null and
            i.indexed is null
            
            """
limit = 100000
for df in tqdm(cpd.read_sql_query(query, engine, chunksize=limit), desc="milvus_update"):
    df = df.rename(columns = {'id':'food_id'})
    df = df[['food_id','clip']]
    collection.insert(df)
    to_insert = df[['food_id']].rename(columns = {'food_id':'id'})
    to_insert['indexed'] = True
    to_insert.to_sql("indexed",engine,index=False,if_exists = 'append',method = 'multi')