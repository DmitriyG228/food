from tendo import singleton
me = singleton.SingleInstance()

import os
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
from reai.tools import *
from reai.psql import *
from reai.paths import *
from PIL import Image
from reai.clipmodel import images2clip
import custom_pandas as cpd
from tqdm import tqdm

logger = get_logger('inference')
logger.debug('starting')
query = """select p.id
             from photos_new p
             left join clips_new c on (p.id = c.id)
            where p.downloaded = true and c.clip is Null """

bs = 16



try:
    # total = engine.execute(f'select count(*) from ({query}) a').one()
    total = [20000000]


    pd_iter = cpd.read_sql_query(query, engine, chunksize=bs, index_col='id')

    for inp in tqdm(pd_iter, desc="clip image inference", total=total[0] // bs):  

        try:
            img_list = [photos_resized_path/f'{get_hash_folder(id)}/{id}.jpg' for id in inp.index]
            images = [Image.open(fname) for fname in img_list]
            clip = images2clip(images).numpy().tolist()
            inp['clip'] = clip
            inp.to_sql('clips_new', engine, index_label='id', if_exists='append')

        except Exception as e:
            print(e)
            logger.error(str(e))


except Exception as e:
    print(e)
    logger.error(str(e))
    raise (e)

