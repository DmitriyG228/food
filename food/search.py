# AUTOGENERATED! DO NOT EDIT! File to edit: 01_search.ipynb (unless otherwise specified).

__all__ = ['cos', 'collection_name', 'table', 'foods', 'foods', 'read_image_from_url', 'search_image_', 'series2tensor',
           'multiply_vector', 'drop_vector', 'multiple_foods', 'search_image']

# Cell
from .tools import *
from .paths import *
from .psql import *
import requests
from .qdrant import *
import torch
from torch.nn import CosineSimilarity
cos = CosineSimilarity(dim=1, eps=1e-08)
import numpy as np

# Cell
## temp while api is not aperational
# from food.clipmodel import *
from PIL import Image

# Cell
collection_name = 'food_images'
table = 'foods_prompted'
foods = read_sql(table)
foods = foods.set_index('id')

# Cell
def read_image_from_url(url=None,path=None):
    if url: response = requests.get(url, stream=True)
    if path: pass
    return Image.open(response.raw)



# Cell
def search_image_(url=None,head = 1,env='dev'):
    client = dev_client if env == 'dev' else prod_client
    image_clip = requests.post(f'https://guru.skynet.center/image2vector/?url={url}').json()
    results = client.search(collection_name=collection_name,query_vector=image_clip,top=head)
    image_clip = torch.Tensor(image_clip)
    df = foods.loc[[r.id for r in results]].copy()
    df['score'] = [r.score for r in results]
    df = df.sort_values('score',ascending=False)

    return image_clip,df.reset_index()

series2tensor = lambda series:torch.tensor([np.array(c) for c in series.values])

# Cell
drop_vector =      lambda clip, i: torch.cat([clip[0:i], clip[i+1:]])

def multiply_vector(clip,i,n=1):
    duplicated = torch.cat([clip[i].reshape(1,768) for _ in range(n)])
    return torch.cat([clip, duplicated.reshape(n,768)])

# Cell
def multiple_foods(url,env='dev'):

    image_clip,selected = search_image_(url,head=100,env=env)
    selected=selected.reset_index(drop=True)
    clip = series2tensor(selected['clip'])
    initscore = float(cos(image_clip.reshape(1,768), clip.mean(0).reshape(1,768)).detach().clone())
    startscore = initscore-0.0000001
    n=0

    while startscore !=initscore:
        startscore = initscore

        selected = selected.reset_index(drop=True)
        for i in reversed(selected.index):
            clip = series2tensor(selected['clip'])
            dropped = drop_vector(clip,i)
            testscore = float(cos(image_clip.reshape(1,768), dropped.mean(0).reshape(1,768)).detach().clone())

            if testscore > initscore-0.0001:
                r = selected.loc[i,'text']
                selected = selected.drop(i)
                initscore = testscore

            else:
                extra = multiply_vector(clip,i,1)
                testscore = float(cos(image_clip.reshape(1,768), extra.mean(0).reshape(1,768)).detach().clone())
                if testscore > initscore:
                    selected = selected.append(selected.loc[i])
                    initscore = testscore

            n+=1
            if n ==15:break

        print(initscore)
    count = selected.groupby('text')['clip'].count().sort_index()
    r = selected.drop_duplicates('text').set_index("text").sort_index()
    r['count'] = count
    r = r.sort_values('count',ascending = False)
    r['cumcount'] = r['count'].cumsum()/r['count'].sum()

    description = '. '.join(r[r['cumcount']<0.9]['description'].unique().tolist())


    return r.drop(columns = ['clip']), description, selected,initscore


# Cell
def search_image(url,env='dev'):
    r, desc, sel,score = multiple_foods(url,env=env)
    df = sel[['energy','protein','carb','fat','score']].mean().to_frame().T
    df['score'] =score
    df['description'] = desc
    return df.round()
