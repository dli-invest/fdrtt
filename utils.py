import os
import requests
import json
from icecream import ic, colorizedStderrPrint

LOG_FILE = "log.txt"
def writeToLog(s):
    # write to log file
    colorizedStderrPrint(s)
    with open(LOG_FILE, "a") as f:
        f.write(s)
        f.write("\n")
        f.close()

ic.configureOutput(outputFunction=writeToLog)

def send_discord_file(filename = None, file = None):
    url = os.getenv("DISCORD_WEBHOOK")
    if url == None:
        print('DISCORD_WEBHOOK Missing')
        pass

    files = {'file': (filename, file, 'application/json')}
    if filename != None and file != None:
        requests.post(
            url, files=files
        )

def send_discord_msg(data):
    url = os.getenv("DISCORD_WEBHOOK")
    if url == None:
        print('DISCORD_WEBHOOK Missing')
        pass
    # TODO figure out how to post to threads
    ic("Trying to send discord message")
    # try:
    #     print("TRY TO SEND")
    r = requests.post(
            url, json=data
        )
    data = r.text
    # except Exception as e:
    #     ic("FAILED TO SEND MESSAGE")
    #     print("FAILED TO SEND REQUEST")
    #     print(e)
    #     pass

    # exit(1)

