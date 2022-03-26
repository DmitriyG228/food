# cd; conda activate food; cd food; python 0_food_app.py &>>$HOME/arb_data/output/app1.log & disown
from tendo import singleton
me = singleton.SingleInstance()

import pandas as pd
import numpy as np
from food.tools import *
from food.psql import *
from food.paths import *

from time import sleep

######default_exp psql

from food.tools import docker_container
import os
os.environ['MKL_THREADING_LAYER'] = 'GNU'
import schedule
from pathlib import Path
import os
from functools import partial

bash_command       = lambda x : os.system(f'cd $HOME/food; conda run -n food python "{x}".py &>>$HOME/arb_data/output/"{x}".log')
kill_command       = lambda x : os.system(f'pkill -f {x}')
scheduler = schedule.Scheduler()

constant_procs = ['bot','milvus_update','inference']
[scheduler.every(5).seconds.do(partial(bash_command,p)) for p in constant_procs]

while True: 
    scheduler.run_pending()
    sleep(5)

