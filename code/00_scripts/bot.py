from tendo import singleton
me = singleton.SingleInstance()

import sys
sys.path.insert(0,'..')
from food.bot import *

if __name__ == '__main__': executor.start_polling(dp)