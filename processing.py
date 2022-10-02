"""
    Video processing and text extraction
"""
import time
import json
import subprocess
import os
import math
import glob
import requests
import ffmpeg
import whisper
from utils import ic, writeToLogAndPrint

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
    ic("[get_video_from_start] Getting video")
    # delete filename if it exists
    if os.path.exists(filename):
        os.remove(filename)
    #  f"-{start}", readd live stream index later
    
    result = subprocess.run(
    f'ffmpeg -i "{url}" -t {end} {filename}'
    # ["ffmpeg", "-i", f"'{url}'", "-t", end, "-copy", filename]
    , shell=True, capture_output=True)
    print("do something here")
    ic(result)
    return result.stdout.decode("utf-8")

# wit ai process integration

def convert_mp4_to_mp3(filename: str):
    """
    Convert mp4 to mp3 using ffmpeg
    """
    ic("Converting mp4 to mp3")
    mp4_filename = filename.replace(".mp4", ".mp3")
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
    for i, value in enumerate(lines):
        line = lines[i]
        # make sure this isnt a comment 
        # match { at start of line
        if line.startswith("{") and type_start_line is None:
            type_start_line = i

        if type_start_line is not None and line.startswith("}"):
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
    WIT_AT_HEADERS = {
        'Authorization': f'Bearer {WIT_AT_TOKEN}',
        'Content-Type': mime_type,
        "Accept": "application/json",
    }

    with open(file_path, 'rb') as f:
        WIT_AT_DATA = f.read()
    r = requests.post(WIT_AT_ENDPOINT, headers=WIT_AT_HEADERS, data=WIT_AT_DATA)
    try:
        # writeToLogAndPrint(r.text)
        # print(r.text)
        writeToLogAndPrint("Attempt to parse wit.ai response as json")
        data = r.json()
        return data
    except Exception as _ex:
        ic("Using text logic now")
        return parse_witai_response(r.text)

def format_seconds(seconds: int):
    """
    format seconds to hh:mm:ss
    """
    hours = math.floor(seconds / 3600)
    minutes = math.floor((seconds % 3600) / 60)
    seconds %= 60
    return f"{hours}:{minutes}:{seconds}"

# think I want model loaded and reused?
def get_text_from_mp3_whisper(mp3_file: str):
    model = whisper.load_model("base")
    # options = whisper.DecodingOptions(language="en", without_timestamps=True)
    result = model.transcribe(mp3_file)
    return result


def transcribe_audio_whisper(filename: str, is_livestream: bool = False):
    final_object = {
        "speech": {
            "tokens": []
        },
        "text": "",
    }
    text_bodies = []
    for count, chunk_name in enumerate(split_vid_into_chunks(filename, is_livestream)):
        mp3_file = chunk_name.replace(".mp4", ".mp3")
        print("USING whisper")
        # load audio and pad/trim it to fit 30 seconds
        t2_start = time.perf_counter()
        # try:
        # iterate through files with _{d} format
        final_object = {
            "speech": {
                "tokens": []
            },
            "text": "",
        }
        # get text from mp3
        partial_object = get_text_from_mp3_whisper(chunk_name)
        text_bodies.append({
            "text": partial_object.get("text", ""),
            "count": count,
            "id": chunk_name,
        })
        # except Exception as e:
        #     ic(f"Error getting text from mp3 for {filename}")
        #     ic(e)
        #     return None
    # make final_object, group by number in _{d} format
    final_object = {
        "text": "",
    }
    # sort text_bodies by id number in _{d} format
    text_bodies = sorted(text_bodies, key=lambda k: k['count'])
    for text_body in text_bodies:
        final_object["text"] += text_body.get("text", "")
    # print the recognized text
    return final_object

# for the new system eventually switch to yield
def split_vid_into_chunks(filename: str, is_livestream: bool = False, chunk_size: int = 4*60+30):
    try:
        t1_start = time.perf_counter()
        if not is_livestream:
            # split mp4 into smaller mp3 files
            length_in_secs = get_video_length(filename)
            # round to nearest second 
            length_in_secs = float(length_in_secs)
            length_in_secs = math.ceil(length_in_secs)
            ic(length_in_secs)
            # split into 2 minute 30 second chunks
            chunk_length = chunk_size
            # iterate through chunks
            ic()
            for i in range(math.ceil(length_in_secs /chunk_length)):
                ic()
                # get start and end time
                start = i * chunk_length
                end = (i + 1) * chunk_length
                chunk_filename = filename.replace(".mp4", f"_{i}.mp3")
                # -vn", filename.replace(".mp4", ".mp3")
                # todo integrate directly using ffmpeg python binders
                os.system(f"ffmpeg -y -i {filename} -ss {format_seconds(start)} -t {format_seconds(end)} -vn {chunk_filename}")
                # should wait until this is done
                yield chunk_filename
            ic("No chunks to process for video")
                    # convert_mp4_to_mp3(filename)
        else:
            convert_mp4_to_mp3(filename)
            yield filename
        t2_start = time.perf_counter()
        ic(f"[timing] Converted mp4 to mp3 in {t2_start - t1_start} seconds")
    except Exception as e:
        ic(f"Error converting mp4 to mp3 for {filename}")
        ic(e)
        raise Exception(f"Error converting mp4 to mp3 for {filename}")

def transcribe_audio_wit(filename: str, is_livestream: bool = False):
    """
    Transcribe audio using wit.ai
    """
    final_object = {
        "speech": {
            "tokens": []
        },
        "text": "",
    }

    text_bodies = []
    for count, chunk_name in enumerate(split_vid_into_chunks(filename, is_livestream)):
        # get text from mp3
        t2_start = time.perf_counter()
        # TODO refactor this logic tommorow to be a specific function
        mp3_name = chunk_name.replace(".mp4", ".mp3")
        if not is_livestream:
            # iterate through files with _{d} format
            # get text from mp3
            partial_object = get_text_from_mp3(mp3_name)
            # append to final object
            text_bodies.append({
                "text": partial_object.get("text", ""),
                "id": chunk_name,
                "count": count,
            })
            final_object["text"] += partial_object["text"]
        else:
            # for livestreams we should only have one file
            data = get_text_from_mp3(mp3_name)
            t2_end = time.perf_counter()
            text_bodies.append({
                "text": data.get("text", ""),
                "id": chunk_name,
                "count": count,
            })

    text_bodies = sorted(text_bodies, key=lambda k: k['count'])
    for text_body in text_bodies:
        final_object["text"] += text_body.get("text", "")
    return final_object

def main():
    # data = get_text_from_mp3("livestream5.mp3")
    # print(data)
    # read file from livestream9.json
    # duration = get_video_length("livestream01.mp4")
    t1_start = time.perf_counter()
    data = transcribe_audio_whisper("8F5Mc5bKEdc.mp4", False)
    # output to test text file
    with open("whispers.json", "w") as f:
        f.write(json.dumps(data))
    t1_end = time.perf_counter()
    ic(f"[timing] Transcribed audio in {t1_end - t1_start} seconds")
    # print it in minutes
    ic(f"[timing] Transcribed audio in {(t1_end - t1_start) / 60} minutes")
    
    # t2 for the other transcription
    t2_start = time.perf_counter()
    wit_ai = transcribe_audio_wit("8F5Mc5bKEdc.mp4", False)
    t2_end = time.perf_counter()
    ic(f"[timing] Transcribed audio in {t2_end - t2_start} seconds")
    ic(f"[timing] Transcribed audio in {(t2_end - t2_start) / 60} minutes")
    with open("witai.json", "w") as f:
        f.write(json.dumps(wit_ai))
    # with open("livestream9.json") as f:
    #     data = f.readlines()
    #     data = "".join(data)
    #     resp = parse_witai_response(data)

if __name__ == "__main__":
    main()
