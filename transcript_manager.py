import os
import argparse
from threading import Thread
import time
import json
from operator import itemgetter
from processing import get_video_from_start, transcribe_audio_wit, transcribe_audio_whisper
from utils import get_video_id_from_ytube_url, ic, send_discord_msg, format_time, append_to_github_actions
from yt_utils import get_video_metadata, youtube_livestream_codes, youtube_mp4_codes
from database import DB_MANAGER
import google.generativeai as genai
try:
    MAX_ITERATIONS = os.getenv("MAX_ITERATIONS", "50")
    MAX_ITERATIONS = int(MAX_ITERATIONS)
except Exception as e:
    print(e)
CHUNK_SIZE = 1900
VIDEO_CHUNK_LENGTH_IN_SECS = 4 * 60 + 60
# free delayed real time transcription

class FD_RTT:
    def __init__(self, input_args, config):
        self._config = config
        self.video_url = input_args.get("url")
        # times in seconds, iterations should not be greater than max time
        self.stats = {
            "run_time": 0,
            "start_time": time.time(),
            "iterations": 0,
            "transcriptions": [],
        }
        self.exit_on_video = input_args.get("exit_on_video", True)
        self.metadata = get_video_metadata(self.video_url)
        self.curr_errors = 0
        table_name = os.getenv("TABLE_NAME")
        if table_name is None:
            table_name = input_args.get("table_name")
        if table_name is None:
            table_name = self.get_channel_from_name().replace(" ", "_")
        # fallback to video_id
        if table_name == "" or table_name is None:
            try:
                ic("Grabbing table name from video_id")
                video_id = get_video_id_from_ytube_url(self.video_url)
                self.video_id = video_id
            except Exception as e:
                ic(e)
                ic("Error getting video id")
                self.video_id = ""
        else:
            ic(f"setting table_name from TABLE_NAME as: {table_name}")
            self.video_id = table_name

        self.db_manager = DB_MANAGER()
        try:
            print("Creating table for named: ", self.video_id)
            # create table if it doesn't exist
            self.db_manager.create_tables(self.video_id)
        except Exception as e:
            print(e)
            ic("Failed to make table")
            exit(1)

        global_iteration = os.getenv("ITERATION", "0")
        try:
            global_iteration = int(global_iteration)
        except Exception as e:
            print(e)
            global_iteration = 0

        self.global_iteration = global_iteration

        self.save_to_db = input_args.get("save_to_db", True)

        self.transcribe_tool = input_args.get("transcribe_tool", "whisper")

        # add in video format here
    def get_channel_from_name(self):
        metadata = self.metadata
        channel = metadata.get("channel", "")
        uploader_id = metadata.get("uploader_id", "")
        uploader = metadata.get("uploader", "")
        if uploader == "Yahoo Finance":
            return "YahooFinance"
        if uploader_id == "Bloomberg":
            return "Bloomberg"
        return channel

    def transcribe(self, data: dict):
        """
            takes video file and transcribes it
        """
        filename = data.get("filename", "")
        is_livestream = data.get("is_livestream", True)
        ic(f"Transcribing... {filename}")

        # read config, see if we want to upload to db
        if self.transcribe_tool == "whisper":
            data = transcribe_audio_whisper(filename, is_livestream)
        else:
            data = transcribe_audio_wit(filename, is_livestream)
        if data is not None:
            # save to json file, replace .mp3 with .json
            partial_output = filename.replace(".mp4", ".json")
            # adjust all run times here based on runtime
            curr_run_time = format_time(self.stats['run_time'])
            if self.global_iteration > 0:
                curr_total_time = self.global_iteration * MAX_ITERATIONS * VIDEO_CHUNK_LENGTH_IN_SECS + self.stats["run_time"]
                curr_run_time = format_time(curr_total_time)
            # adjust times in tokens under data
            # TODO fix this for the speech section
            for token in data.get("tokens", []):
                token["start"] = token["start"] + curr_run_time
                token["end"] = token["end"] + curr_run_time

            with open(partial_output, "w", encoding="utf-8", errors="ignore") as f:
                f.write(json.dumps(data, indent=0))
            # append to transcription
            self.stats["transcriptions"].append(data)
            # send_discord_file(filename=partial_output, file=open(partial_output, "rb"))
            text = data.get("text", "")
            curr_iteration = self.global_iteration * MAX_ITERATIONS + self.stats["iterations"]
            self.db_manager.insert_into_db(self.video_id, text, self.video_url, curr_iteration)
            # make function to convert seconds to human readable time
            data = {}
            # adjust runtime based on iteration if available
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
        url = other_data.get("url", "")
        iteration = os.getenv("ITERATION", "0")
        embed = {
            "title": f"{metadata.get('title', '')} - {iteration}",
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

    def parse_metadata(self) -> dict:
        """
        Parse metadata and send to discord.

        After a video is done recording, 
        it will have both the livestream format and the mp4 format.
        """
        # send metadata to discord
        formats = self.metadata.get("formats", [])
        # filter for ext = mp4
        mp4_formats = [f for f in formats if f.get("ext", "") == "mp4"]
        format_ids = [int(f.get("format_id", 0)) for f in mp4_formats]
        if livestream_entries := list(
            set(format_ids).intersection(youtube_livestream_codes)
        ):
            # get the first one
            livestream_entries.sort()
            selected_id = livestream_entries[0]

        video_entries = sorted(set(format_ids).intersection(youtube_mp4_codes))

        is_livestream = True
        if len(video_entries) > 0:
            # use video format id over livestream id if available
            selected_id = video_entries[0]
            is_livestream = False

        # TODO use video format if available


        return {
            "selected_id": selected_id,
            "is_livestream": is_livestream,
        }

    def process_video(self, ytube_url: str = "https://www.youtube.com/watch?v=86YLFOog4GM&ab_channel=SpaceVideos"):
        """
        Main function.
        """
        metadata = self.metadata
        # grab raw data from url with mp3 versions
        formats = metadata.get("formats", [])
        selected_id, is_livestream = itemgetter('selected_id', 'is_livestream')(self.parse_metadata())
        if self.exit_on_video is True and is_livestream is False:
            ic("Exiting on video as it is not a livestream")
            append_to_github_actions("TERMINATE_LIVESTREAM=TRUE")
            exit(0)
        # TODO fix this code so that it can handle non livestreams

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
                    print("ARE YOU EVEN WORKING HERE")
                    self.stats["iterations"] = MAX_ITERATIONS
                    break
                
                ic(f'Iteration: {self.stats.get("iterations", 0)}')
                ic(format_url)
                iterations = self.stats.get("iterations", 0)
                filename = f"{metadata.get('id', '')}_{iterations}.mp4"
                filename = filename.replace("-", "")

                get_video_from_start(format_url, {
                    "end": "0:05:00",
                    "filename": filename,
                })
                background_thread = Thread(target=self.transcribe, args=({"filename": filename, "is_livestream": is_livestream},))
                background_thread.start()
            except Exception as ex:
                # any error, just goes into endless loop
                ic(ex)
                self.curr_errors += 1
                if self.curr_errors > 10:
                    ic("Too many errors, exiting")
                    break
                break
            finally:
                self.stats["iterations"] += 1
                start_time = self.stats["start_time"]
                self.stats["run_time"] = (time.time() - start_time)
                ic(self.stats)
                # every 5 iterations check if we should close
                if self.stats.get("iterations", 0) % 5 == 0 and is_livestream:
                    _, still_is_livestream = itemgetter('selected_id', 'is_livestream')(self.parse_metadata())
                    if still_is_livestream is False:
                        ic("Exiting since livestream is finished")
                        print("LIVESTREAM IS FINISHED")
                        # send message to discord
                        fmtted_run_time = format_time(self.global_iteration * MAX_ITERATIONS * VIDEO_CHUNK_LENGTH_IN_SECS + self.stats['run_time'])
                        data = {"content": f"LIVESTREAM IS FINISHED \n Run time: {fmtted_run_time}"}
                        send_discord_msg(data)
                        append_to_github_actions("TERMINATE_LIVESTREAM=TRUE")
                        exit(0)
                    else:
                        ic("Livestream is still running")

        if self.global_iteration > 0:
            fmtted_run_time = format_time(self.global_iteration * MAX_ITERATIONS * VIDEO_CHUNK_LENGTH_IN_SECS + self.stats['run_time'])
            total_data = {
                "content": f"**Total Run Time** {fmtted_run_time}",
            }
            send_discord_msg(total_data)
        return None

    def summarize_transcriptions_periodically(video_id, gemini_api_key):
        import datetime
        """
        Background thread that periodically summarizes transcriptions from JSON files.

        Args:
            video_id (str): The video ID to filter JSON files.
            gemini_api_key (str): Your Gemini API key.
        """
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-pro')

        try:
            now = datetime.datetime.now()
            one_hour_ago = now - datetime.timedelta(hours=1)
            all_text = ""

            for filename in os.listdir("."):
                if filename.endswith(f"{video_id}.json") and os.path.isfile(filename):
                    file_modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
                    if file_modified_time > one_hour_ago:
                        try:
                            with open(filename, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                all_text += data.get("text", "") + " "
                        except Exception as e:
                            ic(f"Error reading {filename}: {e}")

            if all_text:
                prompt = f"Summarize the following text:\n\n{all_text}"
                try:
                    response = model.generate_content(prompt)
                    summary = response.text
                    data = {"content": f"**Summary of recent transcriptions:**\n{summary}"}
                    send_discord_msg(data)
                except Exception as gemini_error:
                    ic(f"Gemini API error: {gemini_error}")
            else:
                ic("No recent transcriptions found.")

        except Exception as overall_error:
            ic(f"Error summarizing transcriptions: {overall_error}")

def main(params: dict):
    ic("Trying to initialize")
    fd_rtt = FD_RTT(params, {})
    ic("Attempting to run video")
    fd_rtt.process_video(params.get("url"))

if __name__ == "__main__":
    # argparser with one arugment url for youtube videos
    parser = argparse.ArgumentParser(description='Process livestream or audio for youtube video')
    # parser.add_argument('--url', '-id', help='video id', default='https://www.youtube.com/watch?v=dp8PhLsUcFE&ab_channel=BloombergQuicktake%3AOriginals')
    parser.add_argument('--url', '-id', help='video id', default='https://www.youtube.com/watch?v=tZT2MCYu6Zw')
    parser.add_argument('--exit_for_videos', '-efv', help='exit for videos, or non livestreams', default=False)
    # save_to_db
    parser.add_argument('--save_to_db', '-stdb', help='save to db', default=True)
    
    args = parser.parse_args()
    # ensure WIT_AI_TOKEN is set
    ic("Running main")
    # if os.environ.get("WIT_AI_TOKEN") is None:
    #     print("WIT_AI_TOKEN is not set")
    #     exit(1)
    dict_args = {
        "url": args.url,
        "exit_on_video": args.exit_for_videos,
        "save_to_db": args.save_to_db,
    }
    main(dict_args)

    # https://www.youtube.com/watch?v=8F5Mc5bKEdc&ab_channel=CNBCTelevision
