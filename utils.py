import os
import requests
from icecream import ic

LOG_FILE = "log.txt"
def writeToLog(s):
    # write to log file
    # colorizedStderrPrint(s)
    with open(LOG_FILE, "a") as f:
        f.write(s)
        f.write("\n")
        f.close()

ic.configureOutput(outputFunction=writeToLog)

# dont need test cases for this
def send_discord_file(filename = None, file = None):
    url = os.getenv("DISCORD_WEBHOOK")
    if url is None:
        print('DISCORD_WEBHOOK Missing')
    files = {'file': (filename, file, 'application/json')}
    if filename != None and file != None:
        requests.post(
            url, files=files
        )

def send_discord_msg(data):
    url = os.getenv("DISCORD_WEBHOOK")
    if url is None:
        print('DISCORD_WEBHOOK Missing')
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


def writeToLogAndPrint(s: str):
    try:
        writeToLog(s)
        # env var to log to console
        print(s)
    except Exception as e:
        ic()
        ic("Failed to write to log and print")
        print(e)


## format seconds in days, hours
def format_time(seconds: int):
    try:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{days}d {hours}h {minutes}m {seconds}s"
    except Exception as e:
        ic(e)
        ic("Error formatting time")
        return seconds

def get_video_id_from_ytube_url(ytube_url: str):
    try:
        video_id = ytube_url.split("v=")[1].split("&")[0]
        return video_id
    except Exception as e:
        ic(e)
        ic("Error getting video id")
        return ""
