import subprocess
import os
import argparse
from threading import Thread
import time
import requests
import json
from processing import get_video_from_start, transcribe_audio
from utils import ic, send_discord_msg, send_discord_file
from yt_utils import get_video_formats, get_video_link, parse_raw_format_str, youtube_livestream_codes, youtube_mp4_codes

MAX_ITERATIONS = 10
# free delayed real time transcription


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
        # add in video format here

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
            curr_run_time = self.stats["run_time"]
            # adjust times in tokens under data
            # TODO fix this for the speech section
            for token in data.get("tokens", []):
                token["start"] = token["start"] + curr_run_time
                token["end"] = token["end"] + curr_run_time
            with open(partial_output, "w") as f:
               f.write(json.dumps(data, indent=0))
            # append to transcription
            self.stats["transcriptions"].append(data)
            # send_discord_file(filename=partial_output, file=open(partial_output, "rb"))
            text = data.get("text", "")
            # make function to convert seconds to human readable time
            send_discord_msg(message=f"{text}", timestamp=int(curr_run_time))


    def process_video(self, url: str = "https://www.youtube.com/watch?v=86YLFOog4GM&ab_channel=SpaceVideos"):
        """
        Main function.
        """

        # grab raw data from url with mp3 versions
        url = "https://www.youtube.com/watch?v=21X5lGlDOfg&ab_channel=NASA"
        formats = get_video_formats(url)
        
        data = parse_raw_format_str(formats.stdout.decode("utf-8"))
        # check if data has items in mp4 list
        livestream_entries = list(set(data).intersection(youtube_livestream_codes))
        if len(livestream_entries) > 0:
            # get the first one
            lowest_quality = livestream_entries[0]
        else:
            video_entries = list(set(data).intersection(youtube_mp4_codes))
            lowest_quality = video_entries[0]

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
                    "end": 40,
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

    print(fd_rtt.stats["transcriptions"])

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
