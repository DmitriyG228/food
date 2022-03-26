import torch
from transformers import CLIPProcessor, CLIPModel, CLIPTokenizer
from PIL import Image, ImageOps
from multiprocessing import Pool
from functools import partial
from wrapt import synchronized

def img_resize(image, size):
    return ImageOps.fit(image, (size,size), Image.LANCZOS)

def imgs_resize(images, size):
    with Pool(32) as p:
        return p.map(partial(img_resize, size=size), images)

#########################################################################################################################
# en model

en_model_name = 'openai/clip-vit-large-patch14' 

model = CLIPModel.from_pretrained(en_model_name).cuda()
tokenizer = CLIPTokenizer.from_pretrained(en_model_name)
en_processor = CLIPProcessor.from_pretrained(en_model_name)

en_size = model.config.vision_config.image_size
en_dim = model.config.projection_dim

def dict_to_device(d,device):
    for key, value in d.items():
        d[key] = d[key].to(device)
    return d

def norm(v): 
    return v/torch.linalg.norm(v, dim=-1, keepdim=True)

def detach_norm(v):
    v = v.cpu().detach().squeeze()
    return norm(v)

@synchronized
def text2clip_en(text):
    inputs = tokenizer([text],  padding=True, return_tensors="pt")
    inputs = dict_to_device(inputs,'cuda')
    text_features = model.get_text_features(**inputs)
    return detach_norm(text_features)

@synchronized
def images2clip_en(images): 
    images = imgs_resize(images, size=en_size)
    inputs = en_processor(images=images, return_tensors="pt")
    inputs = dict_to_device(inputs,'cuda')
    image_features = model.get_image_features(**inputs)
    return detach_norm(image_features) 

#########################################################################################################################
# mix model

images2clip = images2clip_en

def image2clip(image): return images2clip([image])

text2clip = text2clip_en