# AUTOGENERATED! DO NOT EDIT! File to edit: ../00_nbs/01_search.ipynb.

# %% auto 0
__all__ = ['bad_cats', 'bad_descs', 'bad_keys', 'bad_keys_cat', 'q', 'foods', 'food_clips', 'apply_custom_colormap',
           'get_heatmap', 'blend_array2img', 'search']

# %% ../00_nbs/01_search.ipynb 2
import sys
sys.path.insert(0,'..')
from mytools.tools import *
from .paths import *
from .psql import *
import requests
import torch
import numpy as np
import pandas as pd
from PIL import Image, ImageFont, ImageDraw, ImageEnhance,ImageOps
from .paths import *
# from stego.segment import get_food_segment
from segmentor.segment import *

from mytools.visual import *
from .depth import *

from matplotlib.colors import ListedColormap,LinearSegmentedColormap
import cv2
import numpy as np
from matplotlib import pyplot as plt

# %% ../00_nbs/01_search.ipynb 3
def apply_custom_colormap(image_gray, cmap):

    assert image_gray.dtype == np.uint8, 'must be np.uint8 image'

    # Initialize the matplotlib color map
    sm = plt.cm.ScalarMappable(cmap=cmap)

    # Obtain linear color range
    color_range = sm.to_rgba(np.linspace(0, 1, 256))[:,0:3]    # color range RGBA => RGB
    color_range = (color_range*255.0).astype(np.uint8)         # [0,1] => [0,255]
    # color_range = np.squeeze(np.dstack([color_range[:,2], color_range[:,1], color_range[:,0]]), 0)  # RGB => BGR

    # Apply colormap for each channel individually
    channels = [cv2.LUT(image_gray, color_range[:,i]) for i in range(3)]
    return np.dstack(channels)

# %% ../00_nbs/01_search.ipynb 4
def get_heatmap(arr,
                colors = ["white","lime","green","yellow","orange", "red","purple","purple","purple","purple","purple","purple"],
                values = [0,           1,     50,     100,     200,   300,     400,     500,     600,     700,     800,     900]):
    
    l = list(zip([v/max(values) for v in values],colors))
    cmap=LinearSegmentedColormap.from_list('hmap',l)
    return apply_custom_colormap((np.array(arr)/max(values)*255).astype(np.uint8),cmap)
    

# %% ../00_nbs/01_search.ipynb 5
def blend_array2img(img,arr,alphas = [0.5,0.5]):
    return cv2.addWeighted(arr, alphas[0], np.array(img).astype(np.uint8), alphas[1], 0)

# %% ../00_nbs/01_search.ipynb 6
bad_cats  = ['Vegetables on a sandwich','Candy containing chocolate','Baby juice']
bad_descs = ['Banana, fried']
bad_keys = ['baby food','frozen','juice','drink']
bad_keys_cat = ['formula']

q = """select p.clip, p.text, p.version,f.description,f.category, f.id,f.energy,f.protein,f.carb,f.fat
       from food.foods_prompted as p
       join food.foods as f on (p.food_id = f.id)
       where p.clip is not null
       """


foods = pd.read_sql(q,engine)

# foods = foods.drop(columns = ['clip'])
foods = foods.set_index('id')
foods = foods.dropna()

foods = foods[~foods['category'].isin(bad_cats)]
foods = foods[~foods['description'].isin(bad_descs)]
foods = foods[~foods['description'].str.contains('|'.join(bad_keys))]
foods = foods[~foods['category']   .str.lower().str.contains('|'.join(bad_keys_cat))]

food_clips = series2tensor(foods['clip'])

# %% ../00_nbs/01_search.ipynb 8
### depr
def search(segment_model,url=None,path=None,stego = False, prompt_factor=0.5,min_score=0.22,exand_times =2):
    img = get_image(url=url,path=path)
    img,adj = crop_image_to_square(img,True)
    x_adj,y_adj,size = adj
    
    photo_id = url if url else path.name
    photo_id = photo_id.split('/')[-1]
    
    i = np.asarray(img, dtype="uint8")
    i = np.flip(i,2)
    segmentor_mask = inference_segmentor(segment_model, i)[0]
    segmentor_mask[segmentor_mask!=0]=segmentor_mask[segmentor_mask!=0]+1 



    classes = np.unique(segmentor_mask)[1:]
    classes_ =[]
    urls = []
    for c in classes:
        area = segmentor_mask[segmentor_mask==c].shape[0]
        if area> 20*20:
            class_mask = np.where(segmentor_mask==c,1,0)
            class_mask = expand_boundaries(class_mask,times=exand_times,factor=10)
            img_arr = apply_mask(img,class_mask.T).astype(np.uint8)
            img_arr = crop_zeros(img_arr)
            img_arr[img_arr==[0,0,0]]=255 #replace black with while
            fname = f'{photo_id}_{c}.jpg'
            Image.fromarray(img_arr).save(fragment_reference_images_path/fname)
            urls.append(f'{domain}/fragment_reference_images/{fname}')
            classes_.append(c)
    classes = classes_


    if stego:

        stego_img,stego_mask = get_food_segment(img)

        s = np.copy(segmentor_mask)
        s[s!=0] = 1
        inverse_stego_mask = stego_mask - s
        inverse_stego_mask[inverse_stego_mask==-1]=0
        inverse_stego_img = Image.fromarray(apply_mask(img,inverse_stego_mask).astype(np.uint8))
        ##new
        stego_img        .save(fragment_reference_images_path/f'{photo_id}_stego.jpg')
        inverse_stego_img.save(fragment_reference_images_path/f'{photo_id}_inverse_stego.jpg')
        urls.append(f'{domain}/fragment_reference_images/{photo_id}_inverse_stego.jpg')

    #to push segmented clips towards the whole dish clip

    main_image_url = f'{domain}/fragment_reference_images/{photo_id}_stego.jpg' if stego else url
    main_image_clip = get_image_clip(main_image_url)

    clip_df = pd.DataFrame()
    for u in urls:
        df = search_clip(u,foods,food_clips,prompt_clip=main_image_clip,head = 1,prompt_factor=prompt_factor)[1]
        # df['url'] = u
        clip_df = clip_df.append(df)
    clip_df=clip_df.reset_index(drop=True)
    clip_df['classes'] = classes+[1] if stego else classes
    #new

    clip_df=clip_df[clip_df['score']>min_score]

    mask = torch.Tensor(segmentor_mask)+inverse_stego_mask if stego else torch.Tensor(segmentor_mask)

    dicts =[]
    masks =[]

    attributes = ['energy','protein','carb','fat']
    #create masks of attributes
    for col in attributes:
        dicts.append(clip_df[['classes',col]].set_index("classes")[col].to_dict())
        masks.append(torch.clone(mask))

    areas = {}
    for c in np.unique(mask):
        areas[c]= mask[mask==c].shape[0]

        #clean values where classes are filtered out
        if c not in dicts[0].keys():
            for m in masks:
                m[m==c]=0

    #areas          
    clip_df = clip_df.merge(pd.DataFrame(areas,index = ['area']).T,left_on = 'classes',right_index = True)
    clip_df = clip_df.sort_values('area',ascending = False)

    #assign values to the masks
    for d,m in zip(dicts,masks):
        for k,v in d.items(): m[m == k] = v

    stats = pd.DataFrame([float(m[m!=0].mean()) for m in masks]+[masks[0][masks[0]!=0].shape[0]],
                     index = attributes+['size'])


    img = ImageOps.grayscale(img).convert('RGB')
    blended_img = blend_array2img(img,get_heatmap(masks[0]),alphas=[0.5, 0.9])
    img = Image.fromarray(blended_img[-y_adj:size+y_adj,-x_adj:size+x_adj,:])
    return img,clip_df,masks,urls,stats

# %% ../00_nbs/01_search.ipynb 11
def search(segment_model,path=None, prompt_factor=0.5,min_score=0.22,exand_times =2):
    img = get_image(path=path)
    img,adj = crop_image_to_square(img,True)
    x_adj,y_adj,size = adj

    photo_id = path.name.split('/')[-1]

    i = np.asarray(img, dtype="uint8")
    i = np.flip(i,2)
    segmentor_mask = inference_segmentor(segment_model, i)[0]
    segmentor_mask[segmentor_mask!=0]=segmentor_mask[segmentor_mask!=0]+1 
    classes = np.unique(segmentor_mask)[1:]
    classes_ =[]

    paths = []
    for c in classes:
        area = segmentor_mask[segmentor_mask==c].shape[0]
        if area> 20*20:
            class_mask = np.where(segmentor_mask==c,1,0)
            class_mask = expand_boundaries(class_mask,times=exand_times,factor=10)
            img_arr = apply_mask(img,class_mask.T).astype(np.uint8)
            img_arr = crop_zeros(img_arr)
            img_arr[img_arr==[0,0,0]]=255 #replace black with while
            fname = f'{photo_id}_{c}.jpg'
            p = fragment_reference_images_path/fname
            paths.append(p)
            Image.fromarray(img_arr).save(p)
            classes_.append(c)
    classes = classes_
    
    if prompt_factor >0: paths = [path]+paths

    clips =torch.Tensor(get_image_clip_from_paths(paths))

    if prompt_factor>0:
        prompt_clip = clips[0]
        clips = clips[1:]
        diff = prompt_clip - clips
        clips = clips + diff*prompt_factor

    dfs = []

    for clip in clips:
        df = foods.copy()
        df['score'] = cos(food_clips,clip)
        dfs.append(df.sort_values('score',ascending=False)[:1])

    clip_df = pd.concat(dfs)
    clip_df['classes'] = classes

    clip_df=clip_df[clip_df['score']>min_score]

    mask = torch.Tensor(segmentor_mask)

    dicts =[]
    masks =[]

    attributes = ['energy','protein','carb','fat']
    #create masks of attributes
    for col in attributes:
        dicts.append(clip_df[['classes',col]].set_index("classes")[col].to_dict())
        masks.append(torch.clone(mask))

    areas = {}
    for c in np.unique(mask):
        areas[c]= mask[mask==c].shape[0]

        #clean values where classes are filtered out
        if c not in dicts[0].keys():
            for m in masks:
                m[m==c]=0

    #areas          
    clip_df = clip_df.merge(pd.DataFrame(areas,index = ['area']).T,left_on = 'classes',right_index = True)
    clip_df = clip_df.sort_values('area',ascending = False)

    #assign values to the masks
    for d,m in zip(dicts,masks):
        for k,v in d.items(): m[m == k] = v

    stats = pd.DataFrame([float(m[m!=0].mean()) for m in masks]+[masks[0][masks[0]!=0].shape[0]],
                     index = attributes+['size'])


    img = ImageOps.grayscale(img).convert('RGB')
    blended_img = blend_array2img(img,get_heatmap(masks[0]),alphas=[0.5, 0.9])
    img = Image.fromarray(blended_img[-y_adj:size+y_adj,-x_adj:size+x_adj,:])
    return img,clip_df,masks,stats
