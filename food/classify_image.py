# AUTOGENERATED! DO NOT EDIT! File to edit: 01_classfy_image.ipynb (unless otherwise specified).

__all__ = ['cuda_n', 'cos', 'foods', 'clip', 'search_image', 'search_image']

# Cell
from .tools import *
from .paths import *

import pandas as pd
import numpy as np
from .psql import *

# !nbdev_build_lib
import requests
from .clipmodel import image2clip,text2clip
from PIL import Image
import torch

# Cell
cuda_n = 0

# Cell
cos = torch.nn.CosineSimilarity(dim=-1, eps=1e-6)
foods = pd.read_sql('select * from foods',engine)
clip = torch.Tensor(foods['clip']).cuda(cuda_n).type(torch.float16)

# Cell
def search_image(url=None,path=None,milvus=False):
    if url:
        response = requests.get(url, stream=True)
        image = Image.open(response.raw)
    elif path:
        image = Image.open(path)
    image_clip = image2clip(image)
    if milvus:
        results = search_by_clip(clip.numpy())
        df = get_metadata(results[1])
        df['score'] = results[0]
    else:
        df = foods.drop(columns = ['clip'])
        df['score'] = cos(clip, torch.Tensor(image_clip).cuda(cuda_n)).cpu().detach().numpy()
        df = df.sort_values('score',ascending=False).head(1)

    return df

# Cell
def search_image(url=None,path=None):
    if url:
        response = requests.get(url, stream=True)
        image = Image.open(response.raw)
    elif path:
        image = Image.open(path)
    image_clip = image2clip(image)
    df = foods.drop(columns = ['clip'])
    df['score'] = cos(clip, torch.Tensor(image_clip).cuda(cuda_n)).cpu().detach().numpy()
    df = df.sort_values('score',ascending=False).head(1)

    return df