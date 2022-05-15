from tendo import singleton
me = singleton.SingleInstance(1)
from food.tools import *
from food.paths import *
from food.psql import *

import pandas as pd
import numpy as np
from tqdm import tqdm
import food.custom_pandas as cpd

from food.qdrant import *


project_name = "food"
dim = 768
limit = 100000



query = f"""select f.id,f.description, f.clip as clip
        FROM      {project_name}.foods    f
        LEFT JOIN {project_name}.indexed  i  ON (i.id =       f.id)
        
        WHERE clip    is not null and 
              i .indexed is null
        """



for df in tqdm(cpd.read_sql_query(query, engine, chunksize=limit), desc="qdrant_update {project_name}"):

    ids = df['id'].tolist()
    clip = df['clip']
    clip = np.array([np.array(c) for c in clip.values])

    df = df.fillna('0')


    payload = df.drop(columns = ['id','clip']).to_dict('records')

    client.upload_collection(
        collection_name=project_name,
        vectors=clip,
        payload=payload,
        ids=ids,
        parallel=4
    )

    to_insert = df[['id']]
    to_insert['indexed'] = True
    to_insert.to_sql("{project_name}.indexed",engine,index=False,if_exists = 'append',method = 'multi')

