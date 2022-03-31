# AUTOGENERATED! DO NOT EDIT! File to edit: 00_psql.ipynb (unless otherwise specified).

__all__ = ['engine', 'Session', 'session', 'Base', 'du', 'query', 'current', 'kill', 'insert_ignore', 'Foods',
           'Foods_big', 'Bananas', 'Indexed', 'Dishes']

# Cell
from sqlalchemy import create_engine
from sqlalchemy import DateTime
from sqlalchemy import Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Date, String, Text, Float, Boolean, ForeignKey, and_, or_, MetaData
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy import update
from sqlalchemy import desc
import pandas as pd
import datetime
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import select, exists
from IPython.display import clear_output
from sqlalchemy import Column, Integer, String ,DateTime,UniqueConstraint,Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql.sqltypes import *
from sqlalchemy import *
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement #_literal_as_text
from sqlalchemy.ext import compiler
from sqlalchemy.schema import DDLElement
from sqlalchemy.inspection import inspect
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import VARCHAR

from sqlalchemy.dialects.postgresql import JSON

from sqlalchemy.dialects.postgresql import REAL

from sqlalchemy import cast

# Cell
engine = create_engine('postgresql+psycopg2://postgres:KJnbuiwuef89k@localhost/postgres?port=5432',pool_size=64) #new
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Cell
def du(partitions='no'):

    df = query("""SELECT *, pg_size_pretty(total_bytes) AS total
                            , pg_size_pretty(index_bytes) AS INDEX
                            , pg_size_pretty(toast_bytes) AS toast
                            , pg_size_pretty(table_bytes) AS TABLE
                          FROM (
                          SELECT *, total_bytes-index_bytes-COALESCE(toast_bytes,0) AS table_bytes FROM (
                              SELECT c.oid,
                                     nspname AS table_schema,
                                     relname AS TABLE_NAME
                                      , c.reltuples AS row_estimate
                                      , pg_total_relation_size(c.oid) AS total_bytes
                                      , pg_indexes_size(c.oid) AS index_bytes
                                      , pg_total_relation_size(reltoastrelid) AS toast_bytes
                                  FROM pg_class c
                                  LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
                                  WHERE relkind = 'r'
                          ) a
                        ) a;""")
    df = df[['table_schema','table_name','row_estimate','total_bytes','index_bytes']].sort_values('row_estimate',ascending=False)
    df = df[df['table_schema']=='public']
    df['total_bytes']=df['total_bytes']/10**9
    df['index_bytes']=df['index_bytes']/10**9
    df['row_estimate'] = (df['row_estimate']/1000).astype(int)
    df.columns = ['schema','table','mln_rows','total_Gb','index_Gb']

    if   partitions== 'no' : df = df[~df['table'].apply(lambda x: True in [xx.isdigit() for xx in x])]
    elif partitions== 'yes': df = df[ df['table'].apply(lambda x: True in [xx.isdigit() for xx in x])]
    else:                  df = df
    return df.sort_values('index_Gb',ascending=False)

# Cell
query = lambda q: pd.read_sql_query(q,engine)

# Cell
def current():
    return query("SELECT * FROM pg_stat_activity where state = 'active';")[['pid','query_start','state_change','wait_event_type','wait_event','query','backend_type']]

# Cell
def kill(pid):
    return engine.execute(f'SELECT pg_terminate_backend({pid})')

# Cell
def insert_ignore(df,table,update = False, update_cols = None, engine = engine,unique_cols=[]):
    metadata = MetaData()
    metadata.bind = engine
    table = Table(table, metadata, autoload=True)
    primary_keys = [key.name for key in inspect(table).primary_key]
#     unique_cols = [cc.name for c in list(inspect(table).constraints) for cc in c if type(c) == UniqueConstraint]

    insrt_vals = df.to_dict(orient='records')
    insrt_stmnt = insert(table).values(insrt_vals)

    if update    :
        assert update_cols, 'update_cols must be provided if update'
        set_ = {c:getattr(insrt_stmnt.excluded, c) for c in update_cols}
        do_nothing_stmt  = insrt_stmnt.on_conflict_do_update (index_elements=unique_cols,set_=set_)

    else: do_nothing_stmt  = insrt_stmnt.on_conflict_do_nothing(index_elements=unique_cols)

    engine.execute(do_nothing_stmt)

# Cell
class Foods (Base):
    __tablename__ = 'foods'
    id                  = Column(BIGINT, primary_key=True)
    name                = Column(String)
    clip                = Column(ARRAY(REAL),          nullable=True)

# Cell
class Foods_big (Base):
    __tablename__ = 'foods_big'
    id                  = Column(BIGINT,   primary_key=True, autoincrement = True)
    product_name        = Column(String,          nullable=True,unique=True)
    keywords            = Column(String,          nullable=True)
    ingredients_text    = Column(String,          nullable=True)
    categories          = Column(String,          nullable=True)
    food_groups         = Column(String,          nullable=True)
    energy_kcal_100g    = Column(Float,          nullable=True)
    proteins_100g       = Column(Float,          nullable=True)
    fat_100g            = Column(Float,          nullable=True)
    carbohydrates_100g  = Column(Float,          nullable=True)
    clip                = Column(ARRAY(REAL),          nullable=True)

# Cell
class Bananas (Base):
    __tablename__ = 'bananas'
    id                  = Column(BIGINT,   primary_key=True, autoincrement = True)
    product_name        = Column(String,          nullable=True,unique=True)
    keywords            = Column(String,          nullable=True)
    ingredients_text    = Column(String,          nullable=True)
    categories          = Column(String,          nullable=True)
    food_groups         = Column(String,          nullable=True)
    energy_kcal_100g    = Column(Float,          nullable=True)
    proteins_100g       = Column(Float,          nullable=True)
    fat_100g            = Column(Float,          nullable=True)
    carbohydrates_100g  = Column(Float,          nullable=True)
    clip1                = Column(ARRAY(REAL),          nullable=True)
    clip2                = Column(ARRAY(REAL),          nullable=True)
    clip3                = Column(ARRAY(REAL),          nullable=True)
    clip4                = Column(ARRAY(REAL),          nullable=True)

# Cell
class Indexed (Base):
    __tablename__ = 'indexed'
    id                   = Column(BIGINT,  primary_key=True)
    indexed              = Column(Boolean, nullable   =False)

# Cell
class Dishes (Base):
    __tablename__ = 'dishes'
    id                   = Column(BIGINT,  primary_key=True, autoincrement = True)
    energy_kcal          = Column(Float,   nullable=False)
    proteins             = Column(Float,   nullable=False)
    fat                  = Column(Float,   nullable=False)
    carbohydrates        = Column(Float,   nullable=False)
    ids                  = Column(ARRAY(Integer), nullable=False)
    scores               = Column(ARRAY(Float), nullable=False)
    image_url            = Column(String,  nullable=False)
    user_id              = Column(BIGINT,  primary_key=False)
    grams                = Column(Integer,  primary_key=False)
    timestamp            = Column(DateTime, nullable=False)

