# workflow dispatch event using requests

import requests
import os 
import argparse

def dispatch_github_event(args: dict):
    """
    convert curl to requests
    curl \
    -X POST \
    -H "Accept: application/vnd.github+json" \ 
    -H "Authorization: token <TOKEN>" \
    https://api.github.com/repos/OWNER/REPO/actions/workflows/WORKFLOW_ID/dispatches \
    -d '{"ref":"topic-branch","inputs":{"name":"Mona the Octocat","home":"San Francisco, CA"}}'
    """
    token = os.environ.get("GH_WORKFLOW_TOKEN", "")
    if args.url is None:
        url = "https://api.github.com/repos/dli-invest/fdrtt/actions/workflows/transcribe_video.yml/dispatches"
    else:
        url = args.url
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }
    # get ${{ github.event.inputs.youtube_url }} from env vars
    data = {
        "ref": "main",
        "inputs": {
            "youtube_url": args.youtube_url,
            "iteration": f"{int(args.iteration) + 1}",
        },
    }

    if args.get("table_name"):
        data["inputs"]["table_name"] = args.table_name

    r = requests.post(url, headers=headers, json=data)
    print(r.text)
    print(r.status_code)

if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(description='Dispatch a workflow event')
    parser.add_argument('-url', '--youtube_url', help='youtube_url', required=True)
    parser.add_argument('-i', '--iteration', help='iteration', required=False, default=0)
    parser.add_argument('-u', '--url', help='url', required=False, default="https://api.github.com/repos/dli-invest/fdrtt/actions/workflows/transcribe_video.yml/dispatches")
    args = parser.parse_args()
    dispatch_github_event(vars(args))
