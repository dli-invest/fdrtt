import os
import requests
from icecream import ic, colorizedStderrPrint

LOG_FILE = "log.txt"
def writeToLog(s):
    # write to log file
    # colorizedStderrPrint(s)
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

def send_discord_msg(message = None, timestamp = None):
    url = os.getenv("DISCORD_WEBHOOK")
    # TODO figure out how to post to threads
    data = {}
    if message != None:
        data['content'] = f"**{timestamp}**\n{message}"
        requests.post(
            url, data=data
        )
