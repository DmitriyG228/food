# AUTOGENERATED! DO NOT EDIT! File to edit: 00_search_glovo.ipynb (unless otherwise specified).

__all__ = ['project_name', 'client', 'prep_params', 'prep_consitions', 'search_by_clip', 'search_by_text', 'id_table',
           'get_metadata']

# Cell
import pandas as pd
import numpy as np
from .tools import *
from .psql import *
from .paths import *
from sqlalchemy import Table,BIGINT,Column
from qdrant_client import QdrantClient
from .qdrant import *
from qdrant_client.http.models import Filter, FieldCondition, Range

import numpy as np
import requests

project_name = 'glovo'
client = dev_client

# Cell
def prep_params(params):
    df = pd.DataFrame([params]).T.reset_index()
    params_df = df['index'].str.split('_', expand=True)
    params_df.columns = ['cond','key']
    return params_df.join(df[0].to_frame('value')).sort_values('cond')

def prep_consitions(params):
    params = prep_params(params)
    keys = params['key'].unique()
    conditions = []


    for key in keys:
        param = params[params['key'] == key]

        if param['cond'].tolist() == ['max','min']: # both min and max prepsent
            conditions.append(FieldCondition(
                    key=key,
                    range=Range(
                        gte=param[param['cond']=='min']['value'].iloc[0],
                        lte=param[param['cond']=='max']['value'].iloc[0]
                    )
                ))

        elif param['cond'].tolist() == ['max']: # both min and max prepsent
            conditions.append(FieldCondition(
                    key=key,
                    range=Range(
                        lte=param[param['cond']=='max']['value'].iloc[0]
                    )
                ))

        elif param['cond'].tolist() == ['min']: # both min and max prepsent
            conditions.append(FieldCondition(
                    key=key,
                    range=Range(
                        gte=param[param['cond']=='min']['value'].iloc[0]
                    )
                ))

    return conditions

# Cell
def search_by_clip(collection_name,clip, topk,params={}):

    # query_filter = Filter(must=prep_consitions(params)) if len(params)>0 else None
    results = client.search(collection_name=collection_name,query_vector=clip,top=topk)#,query_filter=query_filter)
    return [r.score for r in results], [r.id for r in results]

# Cell
def search_by_text(text,topk=5,params={},prompt = None,prompt_factor=3,collection_name=project_name,return_clip = False):
    clip = np.array(requests.post(f'https://guru.skynet.center/text2vector/?text={text}').json())
    if prompt:
        prompt_clip = np.array(requests.post(f'https://guru.skynet.center/text2vector/?text={prompt+text}').json())
        diff = prompt_clip - clip
        clip = clip + diff*prompt_factor
    results = search_by_clip(collection_name,clip, topk,params)
    df = get_metadata(results[1],return_clip)
    df['accuracy'] =results[0]
    df['url'] = df.apply(lambda x: f"http://glovo.away.guru/photos_resized/{x['path']}",axis=1)

    return df
id_table = Table('ids_meta',Base.metadata,Column('id', BIGINT),extend_existing=True)

# Cell
def get_metadata(ids,return_clip = False):
    session = Session()
    session.execute('CREATE TEMPORARY TABLE ids_meta(id bigint) ON COMMIT DROP')
    stmt = id_table.insert([{'id':t} for t in ids])
    session.execute(stmt)

    if return_clip:
        q = f"""select country_code,city_code,store_name,product_name,collection_section,product_description, path, clip
                FROM {project_name}.photos p
                join {project_name}.clips c on (p.id = c.id)
                INNER JOIN ids_meta             m  ON (p.id =      m.id)"""

    else:
        q = f"""select country_code,city_code,store_name,product_name,collection_section,product_description, path
                                    FROM {project_name}.photos p
                                    INNER JOIN ids_meta             m  ON (p.id =      m.id)"""

    df = pd.read_sql(q,session.connection())
    session.close()
    return df
