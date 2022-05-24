# AUTOGENERATED! DO NOT EDIT! File to edit: 01_search.ipynb (unless otherwise specified).

__all__ = ['foods', 'foods', 'search_image', 'foods', 'foods', 'read_image_from_url', 'search_image']

# Cell
from .tools import *
from .paths import *
from .psql import *
import requests
from .qdrant import *

# Cell
foods = read_sql('foods')
# foods = foods.drop(columns = ['clip'])
foods = foods.set_index('id')

# Cell
def search_image(url=None,head = 1):
    image_clip = requests.post(url).json()
    results = client.search(collection_name=collection_name,query_vector=image_clip,top=head)
    df = foods.loc[[r.id for r in results]].copy()
    df['score'] = [r.score for r in results]
    df = df.sort_values('score',ascending=False)

    return df.reset_index()

# Cell
from .tools import *
from .paths import *
from .psql import *
import requests
from .qdrant import *

# Cell
## temp while api is not aperational
from .clipmodel import *
from PIL import Image

# Cell
foods = read_sql('foods')
# foods = foods.drop(columns = ['clip'])
foods = foods.set_index('id')

# Cell
def read_image_from_url(url=None):
    response = requests.get(url, stream=True)
    return Image.open(response.raw)


# Cell
def search_image(url=None,head = 1):
    image_clip = image2clip(read_image_from_url(url)).tolist()
    # image_clip = requests.post(f'http://127.0.0.1:8181/image2vector/?url={url}').json()
    results = client.search(collection_name=collection_name,query_vector=image_clip,top=head)
    df = foods.loc[[r.id for r in results]]
    df['score'] = [r.score for r in results]
    df = df.sort_values('score',ascending=False)

    return df.reset_index()