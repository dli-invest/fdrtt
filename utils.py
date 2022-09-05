import os
import requests
import logging 
from icecream import ic
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(
    level=logging.INFO,        # Capture info and above as breadcrumbs
    event_level=logging.ERROR  # Send errors as events
)

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    traces_sample_rate=1.0,
    environment="production",
     integrations=[
        sentry_logging,
    ],
)

LOG_FILE = "log.txt"
def writeToLog(s):
    # write to sentry   
    # write to log file
    logging.warning(s)
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