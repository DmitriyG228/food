# AUTOGENERATED! DO NOT EDIT! File to edit: ../00_nbs/0_food_app.ipynb.

# %% auto 0
__all__ = ['me', 'bash_command', 'kill_command', 'scheduler', 'constant_procs']

# %% ../00_nbs/0_food_app.ipynb 4
# cd; conda activate food_product; cd food_prod; python 0_food_app.py &>>$HOME/app1.log & disown

from tendo import singleton
me = singleton.SingleInstance()

import pandas as pd
import numpy as np
from mytools.tools import *
from .psql import *
from .paths import *

from time import sleep

######default_exp psql

import os
os.environ['MKL_THREADING_LAYER'] = 'GNU'
import schedule
from pathlib import Path
import os
from functools import partial

bash_command       = lambda x : os.system(f'cd ; conda run -n {env} python $HOME/{location}/00_scripts/"{x}".py &>>$HOME/output/"{x}".log')
kill_command       = lambda x : os.system(f'pkill -f {x}')


scheduler = schedule.Scheduler()

constant_procs = ['bot']


[scheduler.every(5).seconds.do(partial(bash_command,p)) for p in constant_procs]