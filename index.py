import time
import json
import os
from member_link import member_links
import subprocess
import live_download

FETCHED_JSON = "fetched.json"
fetched = {}


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
            print(time.time() - fetched[link]['timestamp'])
            if time.time() - fetched[link]['timestamp'] > 43200:
                removal.append(link)
        for link in removal:
            print("Expired, Removing " + link)
            del fetched[link]
            print(fetched)
    # Saving json
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
            fetched = {member_links()}
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

    private_download.download(fetched.keys())



if __name__ == '__main__':
    main()
    clear_link()
    time.sleep(10)
    print(time.time())