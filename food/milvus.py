# AUTOGENERATED! DO NOT EDIT! File to edit: 04_milvus.ipynb (unless otherwise specified).

__all__ = ['collection_name', 'dim', 'default_fields', 'default_schema', 'collection', 'default_index']

# Cell
from .tools import *
from .paths import *
from .psql import *

import pandas as pd
import numpy as np

import pandas as pd
import numpy as n
from .tools import *
from .psql import *
from .paths import *
from tqdm import tqdm

from sqlalchemy import Table, Column,BIGINT

import tempfile
from pymilvus import *
collection_name = "food"


# Cell
connections.connect(host="127.0.0.1", port=19533)

dim = 768
default_fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
    FieldSchema(name="clip", dtype=DataType.FLOAT_VECTOR, dim=dim),

]
default_schema = CollectionSchema(fields=default_fields, description="Image collection")

collection = Collection(name=collection_name, schema=default_schema)


# Cell
collection.num_entities

# Cell
default_index = {"index_type": "RHNSW_SQ",
                 "params": {'efConstruction':64, 'M':8},
                 "metric_type": "IP"}