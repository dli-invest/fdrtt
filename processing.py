"""
    Video processing and text extraction
"""
import subprocess
import os
import requests
import time
import json
from utils import ic

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
    ic("Getting video")
    # delete filename if it exists
    if os.path.exists(filename):
        os.remove(filename)
    #  f"-{start}", readd live stream index later
    result = subprocess.run(
    f'ffmpeg -i "{url}" -t {end} {filename}'
    # ["ffmpeg", "-i", f"'{url}'", "-t", end, "-copy", filename]
    , capture_output=True)
    ic(result)
    return result.stdout.decode("utf-8")

# wit ai process integration

def convert_mp4_to_mp3(filename: str):
    """
    Convert mp4 to mp3 using ffmpeg
    """
    ic("Converting mp4 to mp3")
    result = subprocess.run(
        ["ffmpeg", "-i", filename, "-vn", filename.replace(".mp4", ".mp3")],
         capture_output=True
    )
    ic(result)
    # throw error if result is not successful
    if result.returncode != 0:
        raise Exception(result.stdout.decode("utf-8"))
    return result.stdout.decode("utf-8")


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
                found_export = False
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
        data = r.json()
        return data
    except Exception as e:
        return parse_witai_response(r.text)

def transcribe_audio(filename: str):
    """
    Transcribe audio using wit.ai
    """
    mp3_file = filename.replace(".mp4", ".mp3")
    try:
        t1_start = time.perf_counter()
        convert_mp4_to_mp3(filename)
        t2_start = time.perf_counter()
        ic(f"[timing] Converted mp4 to mp3 in {t2_start - t1_start} seconds")
    except Exception as e:
        ic(f"Error converting mp4 to mp3 for {filename}")
        ic(e)
        return None

    try:
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
    with open("livestream9.json") as f:
        data = f.readlines()
        data = "".join(data)
        resp = parse_witai_response(data)

if __name__ == "__main__":
    main()
