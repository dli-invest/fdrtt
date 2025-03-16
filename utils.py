import os
import requests
import logging 
from icecream import ic
import datetime

def get_log_file_path():
    """Returns the path to the log file, creating the directory if needed."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    now = datetime.datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    return os.path.join(log_dir, f"log_{date_string}.txt")


def writeToLog(s):
    # write to sentry   
    # write to log file
    
    LOG_FILE = get_log_file_path()
    logging.warning(s)
    # colorizedStderrPrint(s)
    with open(LOG_FILE, "a", errors="ignore") as f:
        f.write(s)
        f.write("\n")
        f.close()

ic.configureOutput(outputFunction=writeToLog)

# dont need test cases for this
def send_discord_file(filename = None, file = None, env_var = "DISCORD_WEBHOOK"):
    url = os.getenv(env_var)
    if url is None:
        print('DISCORD_WEBHOOK Missing')
    files = {'file': (filename, file, 'application/json')}
    if filename != None and file != None:
        requests.post(
            url, files=files
        )

def send_discord_msg(data, env_var = "DISCORD_WEBHOOK"):
    url = os.getenv(env_var)
    if url is None:
        print('DISCORD_WEBHOOK Missing')
    # TODO figure out how to post to threads
    ic("Trying to send discord message")
    # try:
    #     print("TRY TO SEND")
    try:
        r = requests.post(
                url, json=data
            )
        data = r.text
    except Exception as e:
        ic(e)
        ic("Error sending discord message")
    # except Exception as e:
    #     ic(e)
    #     ic("Error sending discord message")

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
        seconds %= 60
        return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
    except Exception as e:
        ic(e)
        ic("Error formatting time")
        return seconds

def get_video_id_from_ytube_url(ytube_url: str):
    try:
        return ytube_url.split("v=")[1].split("&")[0]
    except Exception as e:
        ic(e)
        ic("Error getting video id")
        return ""


def append_to_github_actions(s: str):
    try:
        with open(os.getenv("GITHUB_ENV"), "a") as f:
            f.write(s)
            f.write("\n")
            f.close()
    except Exception as e:
        ic(e)
        ic("Error appending to github actions")