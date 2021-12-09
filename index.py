import time
import json
import os
import live_download
import requests
import re

FETCHED_JSON = "fetched.json"
fetched = {}
"""
fetched = {
    "kson ONAIR": {
        "id": "aXdH11XtikI",
        "downloaded": "false",
        "timestamp": 1631826398.5934074
    },
    "Mio Channel 大神ミオ": {
        "id": "wri4zMtI5sc",
        "downloaded": "false",
        "timestamp": 1631826398.5934074
    }
}
"""


def save():
    with open(FETCHED_JSON, "w", encoding="utf8") as writeFile:
        json.dump(fetched, writeFile, indent=4, ensure_ascii=False)


def clear_link():
    with open(FETCHED_JSON, encoding="utf8") as readFile:
        fetched_json = json.load(readFile)

        removal = []
        for link in fetched_json.keys():
            if time.time() - fetched_json[link]['timestamp'] > 14400:
                removal.append(link)
        for link in removal:
            # Remove link in global fetched and local fetched_json
            if link in fetched.keys():
                del fetched[link]
            print("[INFO] Expired, Removing " + link)
            del fetched_json[link]

    # Saving json if links can be removed
    if len(removal) > 0:
        with open(FETCHED_JSON, "w", encoding="utf8") as writeFile:
            json.dump(fetched_json, writeFile, indent=4, ensure_ascii=False)
            print("[INFO] Saving json")


if os.path.isfile(FETCHED_JSON):
    with open(FETCHED_JSON, encoding="utf8") as f:
        try:
            fetched = json.load(f)
        except json.JSONDecodeError as j:
            print(f"[ERROR] {j}")
            fetched = {}
            save()
else:
    fetched = {}
    save()


def get_links():
    # Channel IDs for other channels i.e. kson, nayuta
    other_channel_ids = ["UC9ruVYPv7yJmV0Rh0NKA-Lw", "UCmhtmUBjkXOAetnaDq-XJ1g"]
    # Use holodex api to grab live streams
    try:
        req = requests.get(url="https://holodex.net/api/v2/live?org=Hololive&status=live").json()
    except requests.exceptions.RequestException as rerror:
        print(["ERROR"], rerror)
        req = []
        pass
    req2 = []
    for channel_id in other_channel_ids:
        try:
            req2 += requests.get(url=f"https://holodex.net/api/v2/live?channel_id={channel_id}&status=live").json()
        except requests.exceptions.RequestException as rerror:
            print(["ERROR"], rerror)
            continue

    combined_data = req + req2
    streams = []
    if len(combined_data) != 0:
        for stream in combined_data:
            if re.search('(member|members)', stream['title'].lower()) or re.search('(メンバ|メン限)', stream['title']):
                streams.append(stream)
    return streams


def download():
    streams = get_links()
    for stream in streams:
        if stream["channel"]["name"] not in fetched.keys():
            fetched[stream["channel"]["name"]] = {'id': stream["id"],
                                                  'downloaded': 'false',
                                                  'timestamp': time.time()}
    save()
    # Get video_id's that have not been downloaded
    download_id = []
    for link in fetched:
        if fetched[link]['downloaded'] == 'false':
            download_id.append(fetched[link]["id"])
    # Download the not downloaded member video if there are videos to download
    if len(download_id) != 0:
        download_result = live_download.download(download_id)
        print(f"[INFO] Downloading {download_id}")
        for downloaded in download_result:
            if fetched[link]["downloaded"]:
                # set fetched video's downloaded key to download's key
                fetched[link]['downloaded'] = download_result[downloaded]
    else:
        print("[INFO] No member's only stream found/downloaded")
        save()


if __name__ == '__main__':
    clear_link()
    # In seconds so 14400sec == 4 hours
    expire_time = 14400
    sleep_time = 300
    while True:
        start_time = time.time()
        if time.time() - start_time > expire_time:
            clear_link()
            start_time = time.time()
        download()
        # change sleep time to 1 min maybe
        print(f"[INFO] Sleeping for {sleep_time} seconds\n")
        time.sleep(sleep_time)
