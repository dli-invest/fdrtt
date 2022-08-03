import subprocess
import os
import argparse
from threading import Thread
import time
import json
from processing import get_video_from_start, transcribe_audio, get_video_length
from utils import ic, send_discord_msg
from yt_utils import get_video_formats, get_video_link, get_video_metadata, parse_raw_format_str, youtube_livestream_codes, youtube_mp4_codes

MAX_ITERATIONS = 60
CHUNK_SIZE = 1900
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

    def transcribe(self, data: dict):
        """
            takes video file and transcribes it
        """
        filename = data.get("filename", "")
        is_livestream = data.get("is_livestream", False)
        ic(f"Transcribing... {filename}")
        data = transcribe_audio(filename, is_livestream)
        ic(data)
        if data is not None:
            # save to json file, replace .mp3 with .json
            partial_output = filename.replace(".mp4", ".json")
            # adjust all run times here based on runtime
            curr_run_time = f"{self.stats['run_time']:.2f}"
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
            data = {}
            data['content'] = f"**{curr_run_time}**\n{text}"
            # split data content into chunks of 1900 characters
            chunks = [data['content'][i:i+CHUNK_SIZE] for i in range(0, len(data['content']), CHUNK_SIZE)]
            for chunk in chunks:
                data['content'] = chunk
                send_discord_msg(data)


    def send_metadata_embed(self, metadata: dict, other_data: dict):
        """
        Send metadata embed to discord
        """
        # data = {
        #     "embeds": [{
        #          "title": "test",
        # }]
        # }
        # format_id = other_data.get("format_id", "")
        # get youtube video from link
        url = other_data.get("url", "")
        embed = {
            "title": f"{metadata.get('title', '')}",
            "description": metadata.get("description", "")[:500],
            "url": url,
            "thumbnail": {"url": metadata.get("thumbnail", "")},
            "fields": [
                {
                    "name": "Livestream",
                    "value": other_data.get("is_livestream", ""),
                    "inline": True,
                }
            ],
        }

        data = {"embeds": [embed]}
        ic("Sending metadata embed")
        send_discord_msg(data)

    def process_video(self, ytube_url: str = "https://www.youtube.com/watch?v=86YLFOog4GM&ab_channel=SpaceVideos"):
        """
        Main function.
        """

        # grab raw data from url with mp3 versions
        metadata = get_video_metadata(ytube_url)
        formats = metadata.get("formats", [])

        # filter for ext = mp4
        mp4_formats = [f for f in formats if f.get("ext", "") == "mp4"]
        format_ids = [int(f.get("format_id", 0)) for f in mp4_formats]
        # sort format ids highest to lowest
        # data = parse_raw_format_str(formats.stdout.decode("utf-8"))
        # check if data has items in mp4 list
        # youtube id from metadata and extension and number
        livestream_entries = list(set(format_ids).intersection(youtube_livestream_codes))
        is_livestream = True
        if livestream_entries:
            # get the first one
            livestream_entries.sort()
            selected_id = livestream_entries[0]
        else:
            video_entries = sorted(set(format_ids).intersection(youtube_mp4_codes))
            selected_id = video_entries[0]
            is_livestream = False

        self.send_metadata_embed(metadata, {"format_id": selected_id, "url": ytube_url, "is_livestream": is_livestream})
        # to prevent link for expiring regrab when possible
        # loop through data and get first number
        while self.stats.get("iterations", 0) < MAX_ITERATIONS:
            try:
                # grab format from formats using format_id
                selected_format = [f for f in formats if f.get("format_id", "") == str(selected_id)][0]
                format_url = selected_format.get("url", "")
                if not is_livestream:
                    filename = f"{metadata.get('id', '')}.mp4"
                    filename = filename.replace("-", "")
                    # get video from start
                    if not os.path.isfile(filename):
                           get_video_from_start(format_url, {
                                "end": "0:15:00",
                                "filename": filename
                            })

                    # transcribe audio
                    self.transcribe({"filename": filename, "is_livestream": is_livestream})
                    break
                ic(f'Iteration: {self.stats.get("iterations", 0)}')
                ic(format_url)
                iterations = self.stats.get("iterations", 0)
                filename = f"{metadata.get('id', '')}_{iterations}.mp4"
                filename = filename.replace("-", "")
                get_video_from_start(format_url, {
                    "end": "0:04:30",
                    "filename": filename,
                })
                background_thread = Thread(target=self.transcribe, args=({"filename": filename, "is_livestream": is_livestream},))
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
        return mp4_formats

def main(url:str):
    fd_rtt = FD_RTT(url, {})
    data = fd_rtt.process_video(url)

    # print(fd_rtt.stats["transcriptions"])

if __name__ == "__main__":
    # argparser with one arugment url for youtube videos
    parser = argparse.ArgumentParser(description='Process livestream or audio for youtube video')
    parser.add_argument('--url', '-id', help='video id', default='https://www.youtube.com/watch?v=dp8PhLsUcFE&ab_channel=BloombergQuicktake%3AOriginals')
    args = parser.parse_args()
    # ensure WIT_AI_TOKEN is set
    if os.environ.get("WIT_AI_TOKEN") is None:
        print("WIT_AI_TOKEN is not set")
        exit(1)
    main(args.url)
