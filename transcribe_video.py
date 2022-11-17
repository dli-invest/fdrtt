# simple script to transcribe videos from a url like dropdown.abs(
import os
import requests
import json
import argparse
from utils import send_discord_msg
from processing import transcribe_audio_whisper

def download_file_from_url(url, filename):
    # open in binary mode
    if os.path.exists(filename):
        os.remove(filename)

    print("downloading video", url)
    with open(filename, "wb") as file:
        # get request
        response = requests.get(url)
        # write to file
        file.write(response.content)


def transcribe_video(url: str):
    # check if url is a local path or a url
    filename = url
    if filename.startswith("http"):
        download_file_from_url(filename, "video.mp4")
        filename = "video.mp4"

    data = transcribe_audio_whisper(filename, False)
    partial_output = filename.replace(".mp4", ".json")

    with open(partial_output, "w", encoding="utf-8", errors="ignore") as f:
        f.write(json.dumps(data, indent=0))

    data = {}
    # adjust runtime based on iteration if available
    # split data content into chunks of 1900 characters
    chunks = [data['content'][i:i+CHUNK_SIZE] for i in range(0, len(data['content']), CHUNK_SIZE)]
    for chunk in chunks:
        data['content'] = chunk
        try:
            send_discord_msg(data)
        except Exception as e:
            return

if __name__ == "__main__":
    # todo add argparser
    parser = argparse.ArgumentParser(description='Process video from url')
    parser.add_argument("--url", help="url where you can download video", default="https://www.dropbox.com/s/jvajeen28clpicy/archive.mp4?dl=1")

    args = parser.parse_args()

    # todo add logging
    transcribe_video(args.url)
