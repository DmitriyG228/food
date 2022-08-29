from tendo import singleton
me = singleton.SingleInstance()

import sys
import os
sys.path.insert(0,'..')
from food.psql import pgdump,schema,passw,port

command =pgdump(schema,passw,port)
print(command)
os.system(command)

