from tendo import singleton
me = singleton.SingleInstance()

from reai.milvus import collection, onehot, default_index
from time import sleep
from reai.tools import from_pickle
from reai.psql import *
import pandas as pd
from tqdm import tqdm
import custom_pandas as cpd

#engine.execute('truncate table indexed')

# city_replace_dict,country_replace_dict = from_pickle('location_dicts.pkl')

limit = 100000

#collection.drop_index()

# query = f"""select c.*, 
#                    l.id as listing_id, l.latitude, l.longitude,l.bedrooms,l.beds, l.price,    
#                    ci.city, ci.country
#         FROM      clips                 c
#         LEFT JOIN photos                p  ON (c.id =       p.id)
#         LEFT JOIN listings              l  ON (l.id =       p.listing_id)
#         LEFT JOIN listings_cities       ci ON (l.id =       ci.listing_id)
#         LEFT JOIN indexed               i  ON (i.id =       p.id)
        
#         WHERE c .clip0    is not null and 
#               ci.country is not null and 
#               p .resized is not null and
#               i .indexed is null
#         """


query = f"""select c.*, 
                   l.id as listing_id, l.latitude, l.longitude,l.bedrooms,l.beds, l.price    
        FROM      clips_new             c
        LEFT JOIN photos_new            p  ON (c.id =       p.id)
        JOIN listings                   l  ON (l.id =       p.listing_id)
        LEFT JOIN indexed               i  ON (i.id =       p.id)
        
        WHERE c .clip    is not null and 
              p .resized is not null and
              i .indexed is null
        """


for df in tqdm(cpd.read_sql_query(query, engine, chunksize=limit), desc="milvus_update"):
    # df['city'] = (df['country'] + ', ' + df['city']).map(lambda x: city_replace_dict.get(x,x))
    # df['country'] = df['country'].map(lambda x: country_replace_dict.get(x,x))
    # df = df.rename(columns = {'id':'pic_id', 'city': 'city_id', 'country': 'country_id'})
    onehot.apply(df, 'clip')
    df = df.rename(columns = {'id':'pic_id'})
    df = df[['pic_id','clip','listing_id','latitude','longitude','bedrooms','beds','price']]
    collection.insert(df)
    to_insert = df[['pic_id']].rename(columns = {'pic_id':'id'})
    to_insert['indexed'] = True
    to_insert.to_sql("indexed",engine,index=False,if_exists = 'append',method = 'multi')

print('data uploaded, building index...')
collection.create_index(field_name="clip", index_params=default_index)
print('index built')
sleep(60*5)


