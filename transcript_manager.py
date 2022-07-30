import subprocess
import os
import argparse
from threading import Thread
import time
import requests
import json
from processing import get_video_from_start, transcribe_audio
from utils import ic
from yt_utils import get_video_formats, get_video_link, parse_raw_format_str

MAX_ITERATIONS = 10
# free delayed real time transcription

def make_discord_request(filename = None, file = None):
    url = os.getenv("DISCORD_WEBHOOK")
    if url == None:
        print('DISCORD_WEBHOOK Missing')
        pass

    files = {'file': (filename, file, 'application/json')}
    if filename != None and file != None:
        resp = requests.post(
            url, files=files
        )

class FD_RTT:
    def __init__(self, url, config):
        self._config = config
        self.url = url
        # times in seconds, iterations should not be greater than max time
        self.stats = {
            "run_time": 0,
            "start_time": time.time(),
            "iterations": 0,
            "transcriptions": [],
        }

    def transcribe(self, filename: str):
        """
            takes video file and transcribes it
        """
        ic(f"Transcribing... {filename}")
        data = transcribe_audio(filename)
        ic(data)
        if data is not None:
            # save to json file, replace .mp3 with .json
            partial_output = filename.replace(".mp4", ".json")
            # adjust all run times here based on runtime
            with open(partial_output, "w") as f:
               f.write(json.dumps(data, indent=0))
            # append to transcription
            self.stats["transcriptions"].append(data)

            make_discord_request(filename=partial_output, file=open(partial_output, "rb"))


    def process_video(self, url: str = "https://www.youtube.com/watch?v=86YLFOog4GM&ab_channel=SpaceVideos"):
        """
        Main function.
        """

        # grab raw data from url with mp3 versions
        url = "https://www.youtube.com/watch?v=21X5lGlDOfg&ab_channel=NASA"
        formats = get_video_formats(url)
        
        data = parse_raw_format_str(formats.stdout.decode("utf-8"))
        # get lowest number first, focus on audio
        # get first number from data
        lowest_quality = data[0]
        # to prevent link for expiring regrab when possible
        # loop through data and get first number
        while self.stats.get("iterations", 0) < MAX_ITERATIONS:
            try:
                ic("Iteration: {}".format(self.stats.get("iterations", 0)))
                result = get_video_link(url, lowest_quality)
                ic(result)
                iterations = self.stats.get("iterations", 0)
                filename = f"livestream{iterations}.mp4"
                get_video_from_start(result, {
                    # "end": 20,
                    "filename": filename,
                })
                background_thread = Thread(target=self.transcribe, args=(filename,))
                background_thread.start()
                # background_thread.join()
                # process video here
                # update iteration in stats
            except Exception as e:
                ic(e)
            finally:
                self.stats["iterations"] += 1
                start_time = self.stats["start_time"]
                self.stats["run_time"] = (time.time() - start_time)
                ic(self.stats)
                # break
        return data

def main(url:str):
    fd_rtt = FD_RTT(url, {})
    data = fd_rtt.process_video(url)

if __name__ == "__main__":
    # argparser with one arugment url for youtube videos
    parser = argparse.ArgumentParser(description='Process livestream or audio for youtube video')
    parser.add_argument('--url', '-id', help='video id', default='https://www.youtube.com/watch?v=enGbgVLMuw4&ab_channel=YahooFinance')
    args = parser.parse_args()
    # ensure WIT_AI_TOKEN is set
    if os.environ.get("WIT_AI_TOKEN") is None:
        print("WIT_AI_TOKEN is not set")
        exit(1)
    main(args.url)
    pass
