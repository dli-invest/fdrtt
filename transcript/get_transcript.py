import json
from youtube_transcript_api import YouTubeTranscriptApi

benchmark = YouTubeTranscriptApi.get_transcript("8F5Mc5bKEdc")

final_object = {
    "text": ""
}

for i in benchmark:
    final_object["text"] = final_object["text"] + i["text"] + " "


# write final_object to a file
with open('transcript.json', 'w') as outfile:
    json.dump(final_object, outfile)