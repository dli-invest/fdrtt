# workflow dispatch event using requests

import requests
import os 
import argparse

"""
convert curl to requests
curl \
  -X POST \
  -H "Accept: application/vnd.github+json" \ 
  -H "Authorization: token <TOKEN>" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/WORKFLOW_ID/dispatches \
  -d '{"ref":"topic-branch","inputs":{"name":"Mona the Octocat","home":"San Francisco, CA"}}'
"""
# parse arguments
parser = argparse.ArgumentParser(description='Dispatch a workflow event')
parser.add_argument('-url', '--youtube_url', help='youtube_url', required=True)
parser.add_argument('-i', '--iteration', help='iteration', required=True)

args = parser.parse_args()
token = os.environ.get("GH_WORKFLOW_TOKEN", "")
url = "https://api.github.com/repos/dli-invest/fdrtt/actions/workflows/transcribe_video.yml/dispatches"
headers = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {token}",
}
# get ${{ github.event.inputs.youtube_url }} from env vars
data = {
    "ref": "main",
    "inputs": {
        "youtube_url": args.youtube_url,
        "iteration": args.iteration,
    },
}
r = requests.post(url, headers=headers, json=data)
print(r.text)
print(r.status_code)