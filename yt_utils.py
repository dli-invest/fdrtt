import subprocess
import re
from utils import ic


def get_video_formats(vid_url: str):
    """
    Returns the raw of video formats available for the given video url.
    """
    result = subprocess.run(f"youtube-dl -F {vid_url}", capture_output=True)
    print("SHOWING RESULTS")
    print(result.stdout)
    return result

def get_video_link(url: str, format_code: str):
    """
    Returns the video link for the given url.
    """
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
    video_formats = [x for x in video_formats if x is not None]
    return video_formats

def parse_video_formats(url: str):
    """
    Parses the raw video formats and returns a list of video formats.
    """
    raw_format_str = get_video_formats(url).stdout.decode("utf-8")
    return parse_raw_format_str(raw_format_str)

def main(url: str = "https://www.youtube.com/watch?v=enGbgVLMuw4&ab_channel=YahooFinance"):
    """
    Main function.
    """
    formats = get_video_formats(url)
    data = parse_raw_format_str(formats.stdout.decode("utf-8"))
    result = get_video_link(url, data[0])
    ic(result)
    return data

if __name__ == "__main__":
    main()