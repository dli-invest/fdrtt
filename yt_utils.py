import subprocess
import re
import time
from typing import List
import youtube_dl
from utils import ic

youtube_livestream_codes = [
    91,
    92,
    93,
    94,
    95,
    96,
    300,
    301,
]
youtube_mp4_codes = [
    298,
    18,
    22,
    140,
    133,
    134
]

def get_video_formats(vid_url: str):
    """
    Returns the raw of video formats available for the given video url.
    """
    result = subprocess.run(f"youtube-dl -F {vid_url}", capture_output=True)
    ic(f"[command] youtube-dl -F {vid_url}")
    return result

def get_video_link(url: str, format_code: str):
    """
    Returns the video link for the given url.
    """
    ic(f"[command] youtube-dl -f {format_code} -g {url}")
    result = subprocess.run(f"youtube-dl -f {format_code} -g {url}", capture_output=True)
    ic(result)
    return result.stdout.decode("utf-8").replace("\n", "")

def find_first_number_in_str(line: str):
    """
    Finds the first number in a string and returns it.
    """
    num = re.findall(r'\d+', line) 
    if len(num) == 0:
        return None
    else:
        return num[0]

def parse_raw_format_str(raw_format_str: str):
    """
    Extracts content from youtube-dl and outputs it to the repo
    [youtube] enGbgVLMuw4: Downloading webpage
    [youtube] enGbgVLMuw4: Downloading m3u8 information
    [youtube] enGbgVLMuw4: Downloading MPD manifest
    [info] Available formats for enGbgVLMuw4:
    format code  extension  resolution note
    91           mp4        256x144    HLS  290k , avc1.42c00b, 15.0fps, mp4a.40.5@ 48k
    92           mp4        426x240    HLS  546k , avc1.4d4015, 30.0fps, mp4a.40.5@ 48k
    93           mp4        640x360    HLS 1209k , avc1.4d401e, 30.0fps, mp4a.40.2@128k
    94           mp4        854x480    HLS 1568k , avc1.4d401f, 30.0fps, mp4a.40.2@128k
    300          mp4        1280x720   4370k , avc1.4d4020, 60.0fps, mp4a.40.2 (best)

    and returns

    [youtube] enGbgVLMuw4: Downloading webpage
    format code  extension  resolution note
    91           mp4        256x144    HLS  290k , avc1.42c00b, 15.0fps, mp4a.40.5@ 48k
    92           mp4        426x240    HLS  546k , avc1.4d4015, 30.0fps, mp4a.40.5@ 48k
    93           mp4        640x360    HLS 1209k , avc1.4d401e, 30.0fps, mp4a.40.2@128k
    94           mp4        854x480    HLS 1568k , avc1.4d401f, 30.0fps, mp4a.40.2@128k
    300          mp4        1280x720   4370k , avc1.4d4020, 60.0fps, mp4a.40.2 (best)
    """
    data = raw_format_str.split("\n")
    # remove lines with [youtube] or [info] or
    clean_data = [x for x in data if not x.startswith("[youtube]") and not x.startswith("[info]")]
    # remove lines with ''
    clean_data = [x for x in clean_data if x != ""]
    # split by commas
    video_formats = [x.split(",")[0] for x in clean_data]
    video_formats = video_formats[1:]
    # extract leading numbers from each line after removing all not digit charcters
    video_formats = [find_first_number_in_str(x) for x in video_formats]
    # remove all Nones from video_formats
    video_formats = [int(x) for x in video_formats if x is not None]
    return video_formats

def parse_video_formats(url: str):
    """
    Parses the raw video formats and returns a list of video formats.
    """
    raw_format_str = get_video_formats(url).stdout.decode("utf-8")
    return parse_raw_format_str(raw_format_str)

# get metadata from youtube-dl
def get_metadata(url: str):
    """
    Returns the metadata of the given url.
    """
    result = subprocess.run(f"youtube-dl -j {url}", capture_output=True)
    ic(f"[command] youtube-dl -j {url}")
    return result

# consider embedding youtube-dl in python instead of the subprocess parsing
def main(url: str = "https://www.youtube.com/watch?v=enGbgVLMuw4&ab_channel=YahooFinance"):
    """
    Main function.
    """
    formats = get_video_formats(url)
    data = parse_raw_format_str(formats.stdout.decode("utf-8"))
    print(data)
    # result = get_video_link(url, data[0])
    # ic(result)
    return

def get_youtube_meta_data(video_url: str)-> List[dict]:
     with youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'}) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
        return info_dict

def get_video_metadata(video_url: str = "https://www.youtube.com/watch?v=21X5lGlDOfg&ab_channel=NASA")-> dict:
    with youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'}) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
        video_title = info_dict.get('title', None)
        uploader_id = info_dict.get('uploader_id', None)
        ic(f"[youtube] {video_title}: {uploader_id}")
    return info_dict

if __name__ == "__main__":
    start = time.time()
    data = get_video_metadata("https://www.youtube.com/watch?v=dp8PhLsUcFE&ab_channel=BloombergQuicktake%3AOriginals")
    print(data)
    end = time.time()
    print(end - start)
    # main()