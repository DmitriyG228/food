stage = 'food_prod'



# cd; conda activate food_product; cd food_prod; python 0_food_app.py &>>$HOME/app1.log & disown
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

bash_command       = lambda x : os.system(f'cd $HOME/{stage}; conda run -n food_product python "{x}".py &>>$HOME/"{x}".log')
kill_command       = lambda x : os.system(f'pkill -f {x}')
start_docker       = lambda x :  docker_container(x).start()


scheduler = schedule.Scheduler()

constant_procs = ['bot']

docker_containers = ['psql_food_prod_1806','qdrant_prod_2206']

[scheduler.every(5).seconds.do(partial(bash_command,p)) for p in constant_procs]
[scheduler.every(5).seconds.do(partial(start_docker,p)) for p in docker_containers]

while True: 
    scheduler.run_pending()
    sleep(5)


