# workflow dispatch event using requests

import requests
import os 
import argparse

# TODO if this keeps failing just dispatch the event from a server
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
    if args.get("url") is None:
        url = "https://api.github.com/repos/dli-invest/fdrtt/actions/workflows/transcribe_video.yml/dispatches"
    else:
        url = args.get("url")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }
    # get ${{ github.event.inputs.youtube_url }} from env vars
    data = {
        "ref": "main",
        "inputs": {
            "youtube_url": args.get("youtube_url"),
            "iteration": f"{int(args.get('iteration', '0')) + 1}",
        },
    }

    if args.get("table_name"):
        data["inputs"]["table_name"] = args.get("table_name")

    print("ATTEMPTING TO DISPATCH GITHUB EVENT")
    try: 
        response = requests.post(url, headers=headers, json=data)
        print(response)
        print(response.text)
    except Exception as e:
        print(e)
        print("ERROR DISPATCHING GITHUB EVENT")
        

if __name__ == "__main__":
    # parse arguments
    print("STARTING TO PARSE ARGUMENTS")
    parser = argparse.ArgumentParser(description='Dispatch a workflow event')
    parser.add_argument('-url', '--youtube_url', help='youtube_url', required=True)
    parser.add_argument('-i', '--iteration', help='iteration', required=False, default=0)
    parser.add_argument('-u', '--url', help='url', required=False, default="https://api.github.com/repos/dli-invest/fdrtt/actions/workflows/transcribe_video.yml/dispatches")
    args = parser.parse_args()
    dict_args = {
        "youtube_url": args.youtube_url,
        "iteration": args.iteration,
        "url": args.url,
    }
    dispatch_github_event(dict_args)
    print("SUCCESFULLY DISPATCHED GITHUB EVENT")
