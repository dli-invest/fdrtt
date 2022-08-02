"""
    Video processing and text extraction
"""
import subprocess
import os
import requests
import time
import json
import ffmpeg
import math
import glob
from utils import ic

def get_video_length(video_path: str):
    """
    Get video length using ffmpeg and return as seconds
    """
    duration = ffmpeg.probe(video_path)
    try:
        return duration["streams"][0]["duration"]
    except Exception as e:
        print(e)
        exit(1)
        return None



def get_video_from_start(url: str, config: dict):
    """
    Get video from start time.
    """
    # result = subprocess.run()
    # could delay start time by a few seconds to just sync up and capture the full video length
    # but would need to time how long it takes to fetch the video using youtube-dl and other adjustments and start a bit before
    start = config.get("start", 0)
    end = config.get("end", "00:00:10")
    filename = config.get("filename", "livestream01.mp4")
    # remove all dashes from filename
    ic("Getting video")
    # delete filename if it exists
    if os.path.exists(filename):
        os.remove(filename)
    #  f"-{start}", readd live stream index later
    
    result = subprocess.run(
    f'ffmpeg -i "{url}" -t {end} {filename}'
    # ["ffmpeg", "-i", f"'{url}'", "-t", end, "-copy", filename]
    , shell=True, capture_output=True)
    ic(result)
    return result.stdout.decode("utf-8")

# wit ai process integration

def convert_mp4_to_mp3(filename: str):
    """
    Convert mp4 to mp3 using ffmpeg
    """
    ic("Converting mp4 to mp3")
    mp4_filename = filename.replace(".mp4", f".mp3")
    result = subprocess.run(
        f"ffmpeg -i {filename} -vn {mp4_filename}",
        shell=True,
    )
    ic(result)
    return result


# parse all the partial json responses and attempt to find the last one

def parse_witai_response(data: str):
    """
    Parse wit.ai response
    """
    # scan for export interface and export type

    type_start_line = None
    type_end_line = None
    matches = []
    lines = data.split("\n")
    for i in range(len(lines)):
        line = lines[i]
        # make sure this isnt a comment 
        # match { at start of line
        if line.startswith("{") and type_start_line is None:
            type_start_line = i

        if type_start_line is not None:
            if line.startswith("}"):
                type_end_line = i
                # append entry to matches
                # get all rows from type_start_line to type_end_line
                matches.append({
                    "type_start": type_start_line,
                    "type_end": type_end_line,
                    "data": lines[type_start_line:type_end_line+1]
                })
                type_start_line = None
                type_end_line = None
                continue
    # combine all data results and remove duplicates and merge text
    final_object = {
        "speech": {
            "tokens": []
        },
        "text": "",
    }
    for match in matches:
        matchstr = "".join(match.get("data"))
        transcript_data = json.loads(matchstr)
        ic(transcript_data)
        # only append entries that has is final
        if transcript_data.get("is_final"):
            # final_object["speech"]["tokens"].append(data)
            final_object["text"] += transcript_data.get("text", "") + " "
            # final_object["text"] += data.get("text", "")
        # else:
        #     final_status = transcript_data.get("is_final")
        #     print("not final", final_status)
    return final_object

def get_text_from_mp3(file_path: str, mime_type = "audio/mpeg3"):
    """
    Get text from video using wit.ai
    """
    WIT_AT_ENDPOINT = 'https://api.wit.ai/dictation?v=20220622'
    WIT_AT_TOKEN = os.environ.get("WIT_AI_TOKEN")
    WIT_AT_HEADERS = {'Authorization': 'Bearer ' + WIT_AT_TOKEN, 'Content-Type': mime_type, "Accept": "application/json"}
    with open(file_path, 'rb') as f:
        WIT_AT_DATA = f.read()
    r = requests.post(WIT_AT_ENDPOINT, headers=WIT_AT_HEADERS, data=WIT_AT_DATA)
    try:
        ic(r.text)
        data = r.json()
        return data
    except Exception as e:
        return parse_witai_response(r.text)

def format_seconds(seconds: int):
    """
    format seconds to hh:mm:ss
    """
    hours = math.floor(seconds / 3600)
    minutes = math.floor((seconds % 3600) / 60)
    seconds = seconds % 60
    return f"{hours}:{minutes}:{seconds}"

def transcribe_audio(filename: str, is_livestream: bool = False):
    """
    Transcribe audio using wit.ai
    """
    mp3_file = filename.replace(".mp4", ".mp3")
    try:
        t1_start = time.perf_counter()
        if is_livestream is False:
            # split mp4 into smaller mp3 files
            length_in_secs = get_video_length(filename)
            # round to nearest second 
            length_in_secs = float(length_in_secs)
            length_in_secs = math.ceil(length_in_secs)
            ic(length_in_secs)
            # split into 4 minute 30 second chunks
            chunk_length = 4 * 60 + 30
            # iterate through chunks
            ic()
            for i in range(0, math.ceil(length_in_secs /chunk_length)):
                ic()
                # get start and end time
                start = i * chunk_length
                end = (i + 1) * chunk_length
                chunk_filename = filename.replace(".mp4", f"_{i}.mp3")
                # -vn", filename.replace(".mp4", ".mp3")
                # todo integrate directly using ffmpeg python binders
                os.system(f"ffmpeg -y -i {filename} -ss {format_seconds(start)} -t {format_seconds(end)} -vn {chunk_filename}")
            else:
                ic("No chunks to process for video")
            # convert_mp4_to_mp3(filename)
        else:
            convert_mp4_to_mp3(filename)
        t2_start = time.perf_counter()
        ic(f"[timing] Converted mp4 to mp3 in {t2_start - t1_start} seconds")
    except Exception as e:
        ic(f"Error converting mp4 to mp3 for {filename}")
        ic(e)
        return None

    # TODO refactor this logic tommorow to be a specific function
    try:
        if is_livestream == True:
            # iterate through files with _{d} format
            final_object = {
                "speech": {
                    "tokens": []
                },
                "text": "",
            }
            for file in glob.glob(f"{filename.replace('.mp4', '_*.mp3')}"):
                # get text from mp3
                partial_object = get_text_from_mp3(file)
                # append to final object
                final_object["speech"]["tokens"] = final_object["speech"]["tokens"] + partial_object["speech"]["tokens"]
                final_object["text"] += partial_object["text"]
            return final_object
        else:
            data = get_text_from_mp3(mp3_file)
            t2_end = time.perf_counter()
            ic(f"[timing] Got text from mp3 in {t2_end - t2_start} seconds")
            return data
    except Exception as e:
        ic(f"Error getting text from mp3 for {filename}")
        ic(e)
        return None

def main():
    # data = get_text_from_mp3("livestream5.mp3")
    # print(data)
    # read file from livestream9.json
    duration = get_video_length("livestream01.mp4")
    # with open("livestream9.json") as f:
    #     data = f.readlines()
    #     data = "".join(data)
    #     resp = parse_witai_response(data)

if __name__ == "__main__":
    main()
