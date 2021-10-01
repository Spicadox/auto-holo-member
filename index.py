import time
import json
import os
from member_link import member_links
import live_download

FETCHED_JSON = "fetched.json"
fetched = {}
"""
fetched = {
    "https://youtube.com/watch?v=aXdH11XtikI": {
        "downloaded": "false",
        "timestamp": 1631826398.5934074
    },
    "https://youtube.com/watch?v=wri4zMtI5sc": {
        "downloaded": "false",
        "timestamp": 1631826398.5934074
    },
    "https://youtube.com/watch?v=ebI3UIEJ3YM": {
        "downloaded": "false",
        "timestamp": 1631829482.364617
    }
}
"""
def save():
    with open(FETCHED_JSON, "w", encoding="utf8") as f:
        print(fetched)
        json.dump(fetched, f, indent=4, ensure_ascii=False)
        print("Saving json")

def clear_link():
    with open(FETCHED_JSON, encoding="utf8") as f:
        fetched = json.load(f)

        removal = []
        for link in fetched.keys():
            if time.time() - fetched[link]['timestamp'] > 14400:
                removal.append(link)
        for link in removal:
            print("Expired, Removing " + link)
            del fetched[link]
            print(fetched)
    # Saving json if links can be removed
    if len(removal) > 0:
        with open(FETCHED_JSON, "w", encoding="utf8") as f:
            print(fetched)
            json.dump(fetched, f, indent=4, ensure_ascii=False)
            print("Saving json")


if os.path.isfile(FETCHED_JSON):
    with open(FETCHED_JSON, encoding="utf8") as f:
        try:
            fetched = json.load(f)
        except json.JSONDecodeError as j:
            print(j)
            fetched = {}
            save()
else:
    fetched = {}
    save()


def main():
    links = member_links()
    for link in links:
        if link not in fetched.keys():
            fetched[link] = {'downloaded': 'false',
                            'timestamp': time.time()}
    save()
    # Get video_id's that have not been downloaded
    download_id = []
    for link in fetched:
        if fetched[link]['downloaded'] == 'false':
            download_id.append(link)
    # Download the undownloaded the member video
    download_result = live_download.download(download_id)
    for download in download_result:
        if fetched[download]:
            # set fetched video's downloaded key to download's key
            fetched[download]['downloaded'] = download_result[download]
    save()


if __name__ == '__main__':
    clear_link()
    while True:
        start_time = time.time()
        if time.time() - start_time > 14400:
            clear_link()
            start_time = time.time()
        main()
        # change sleep time to 1 min maybe
        time.sleep(300)
