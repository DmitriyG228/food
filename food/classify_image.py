# AUTOGENERATED! DO NOT EDIT! File to edit: 01_multiple_foods.ipynb (unless otherwise specified).

__all__ = ['foods', 'foods', 'search_image']

# Cell
from .tools import *
from .paths import *
from .psql import *
import requests
from .qdrant import *

# Cell
foods = read_sql(table)
# foods = foods.drop(columns = ['clip'])
foods = foods.set_index('id')

# Cell
def search_image(url=None,head = 1):
    image_clip = requests.post(f'https://guru.skynet.center/image2vector/?url={url}').json()
    results = client.search(collection_name=collection_name,query_vector=image_clip,top=head)
    image_clip = torch.Tensor(image_clip)
    df = foods.loc[[r.id for r in results]].copy()
    df['score'] = [r.score for r in results]
    df = df.sort_values('score',ascending=False)

    return image_clip,df.reset_index()