from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
from transcript_manager import main as transcript_parser

def main():
    load_dotenv()
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    # Step 2: Find the channel ID for DW News
    channel_response = youtube.search().list(
        q='dwnews',
        type='channel',
        part='id,snippet',
        maxResults=1
    ).execute()

    if not channel_response['items']:
        print("Channel not found.")
        return

    channel_id = channel_response['items'][0]['id']['channelId']

    # Step 3: Search for upcoming livestreams in the DW News channel
    videos_response = youtube.search().list(
        part='id,snippet',
        channelId=channel_id,
        eventType='live',
        type='video',
        maxResults=50,
        order='date'
    ).execute()

    if not videos_response['items']:
        print("No live livestreams found.")
        return

    video_ids = [item['id']['videoId'] for item in videos_response['items']]

    # Step 4: Get detailed video information, including liveStreamingDetails
    video_details_response = youtube.videos().list(
        part='snippet,liveStreamingDetails',
        id=','.join(video_ids)
    ).execute()

    if not video_details_response['items']:
        print("Could not retrieve video details.")
        return

    # Process and print the livestream details
    for item in video_details_response['items']:
        snippet = item['snippet']
        live_details = item.get('liveStreamingDetails', {})

        print(f"Title: {snippet['title']}")
        print(f"Video ID: {item['id']}")
        if live_details:
            print(f"Scheduled Start Time: {live_details.get('scheduledStartTime', 'Not available')}")
            print(f"Actual Start Time: {live_details.get('actualStartTime', 'Not available')}")
            print(f"Actual End Time: {live_details.get('actualEndTime', 'Not available')}")
        else:
            print("Live streaming details not available.")

        print("-" * 20)

        break

    # use last item
    transcript_parser({
        "url": f"https://www.youtube.com/watch?v={item['id']}",
        "exit_on_video": False,
        "save_to_db": True
    })

        # from here trigger

if __name__ == "__main__":
    main()