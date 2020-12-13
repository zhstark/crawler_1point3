import time
import os

def loop():
    while True:
        os.system('sh run.sh')
        time.sleep(8*60*60)

loop()
        