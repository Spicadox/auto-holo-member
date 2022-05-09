import time
import json
import os
from member_link import member_links
import log
import live_download
import requests
import re
import subprocess
import const
# try:
#     import getjson
# except ImportError or ModuleNotFoundError:
#     pass

WEBHOOK_URL = const.WEBHOOK_URL
if const.LOGGING:
    logger = log.create_logger("logfile.log")
try:
    with open('channels.json', 'r', encoding="utf8") as f:
        channels = json.load(f)
except json.JSONDecodeError as jsonError:
    logger.error(jsonError)
    channels = {}
except ValueError as valError:
    logger.error(valError)
    channels = {}
FETCHED_JSON = "fetched.json"
fetched = {}
"""
fetched = {
    "Luna Ch. 姫森ルーナ": {
            "dDT1_BkJdKQ": {
                "downloaded": "true",
                "notified": "true",
                "timestamp": 1652023702.6788592
            }
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
            for id in fetched_json[link].keys():
                if time.time() - fetched_json[link][id]['timestamp'] > 28800:
                    removal.append((link, id))
        for link in removal:
            # Remove link in global fetched and local fetched_json
            if link[0] in fetched.keys():
                # Remove entire object if there is only 1 video id
                if len(fetched[link[0]].keys()) == 1:
                    del fetched[link[0]]
                    del fetched_json[link[0]]
                else:
                    del fetched[link[0]][link[1]]
                    del fetched_json[link[0]][link[1]]
            logger.info(f"Expired, Removing {link[1]} from {link[0]}")

    # Saving json if links can be removed
    if len(removal) > 0:
        with open(FETCHED_JSON, "w", encoding="utf8") as writeFile:
            json.dump(fetched_json, writeFile, indent=4, ensure_ascii=False)
            logger.info("Saving json")
            print(" " * 40, end="\n")


if os.path.isfile(FETCHED_JSON):
    with open(FETCHED_JSON, encoding="utf8") as f:
        try:
            fetched = json.load(f)
        except json.JSONDecodeError as j:
            logger.error(j)
            fetched = {}
            save()
else:
    fetched = {}
    save()


def get_latest_member_streams():
    dict_list = []
    counter = 1
    dict_length = len(channels)
    for channel in channels.values():
        try:
            print(f"[INFO] Looking through member's pages {counter}/{dict_length}...", end="\r")
            command_list = ["yt-dlp", "--cookies-from-browser", "chrome", "--playlist-end", "1", "-j",
                            f"https://www.youtube.com/channel/{channel}/membership"]
            process = subprocess.run(command_list, capture_output=True, text=True)
            # logger.debug(process)

            info_dict = json.loads(process.stdout)

            if info_dict['is_live']:
                dict_list.append({"id": info_dict['id'], "title": info_dict['title'],
                                  "channel": {"name": info_dict['channel']}})
            else:
                continue
        except json.JSONDecodeError as jsonError:
            logger.debug(str(jsonError) + f" occurred when looking through {channel}")
        except Exception as e:
            print(" " * 40, end="\n")
            logger.error(e)
        finally:
            counter += 1
            # time.sleep(4)
    return dict_list


def get_links():
    other_channel_ids = const.other_channel_ids
    api_key = const.API_KEY
    if other_channel_ids is not None:
        channel_ids = "%2".join(other_channel_ids)
    email_links = []
    try:
        if const.FETCH_FROM_EMAIL:
            email_links = member_links()
            logger.debug(email_links)
    except Exception as e:
        # print(" " * 40, end="\n")
        logger.error(e)

    if const.FETCH_FROM_YTDL:
        member_page_links = get_latest_member_streams()

    # Use holodex api to grab live streams
    req = []
    req2 = []
    if const.FETCH_FROM_HOLODEX:
        try:
            req = requests.get(url="https://holodex.net/api/v2/live?org=Hololive&status=live").json()
        except (requests.exceptions.RequestException, json.decoder.JSONDecodeError) as rerror:
            logger.error(rerror)
            logger.error("Something went wrong sending the request")
        try:
            if other_channel_ids is not None or len(other_channel_ids) > 0:
                if api_key is not None:
                    req2 = requests.get(url=f"https://holodex.net/api/v2/users/live?channels={channel_ids}", headers={"X-APIKEYS": api_key}).json()
                else:
                    req2 = requests.get(url=f"https://holodex.net/api/v2/users/live?channels={channel_ids}", headers={"X-APIKEYS": api_key}).json()
        except (requests.exceptions.RequestException, json.decoder.JSONDecodeError) as rerror:
            logger.error(rerror)
            logger.error("Something went wrong sending the request")

    combined_data = req + req2 + email_links
    streams = []
    if len(combined_data) != 0:
        # TODO: download info-json using yt-dlp or save json like auto-ytarchive
        logger.debug(combined_data)
        for stream in combined_data:
            logger.debug(stream)
            # Check the html page to see if it's a member stream
            # if get_is_member_stream(stream["id"]):
            #     steams.append(stream)
            # Return name of the stream in lowercase
            stream_name = stream['title'].lower()
            logger.debug(f"Stream name: {stream_name}")
            member_only = get_is_member_stream(stream['id'])
            logger.debug(member_only)
            if re.search('(member|members)', stream_name) or re.search('(メンバ|メン限)', stream_name) or member_only:
                streams.append(stream)
    streams += member_page_links
    return streams


def notify(name, id):
    try:
        channel_url = "https://www.youtube.com/channel/" + channels[name]
        url = f"https://youtu.be/{id}"
        message = f"[{name}](<{channel_url}>) has a member-only stream live at {url}"
        requests.post(WEBHOOK_URL, json={'content': message})
    except Exception as e:
        # print(" " * 40, end="\n")
        logger.error(e)


def get_is_member_stream(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        # req = urllib.request.Request(url).text
        req = requests.get(url).text
        # logger.debug(req)
        if '"offerId":"sponsors_only_video"' in req:
            return True
        else:
            return False
    except Exception as e:
        # print(" " * 40, end="\n")
        logger.error(e)
        return False


def download():
    streams = get_links()
    for stream in streams:
        streamer_name = stream["channel"]["name"]
        stream_id = stream["id"]
        try:
            import getjson
            url = f"https://youtu.be/{stream_id}"
            getjson.get_json(url)
        except Exception as e:
            logger.error(e)
        # TODO    Take a look and change if statement later
        if stream["channel"]["name"] not in fetched.keys():
            fetched[stream["channel"]["name"]] = {stream["id"]: {
                                                  'downloaded': 'false',
                                                  'notified': 'false',
                                                  'timestamp': time.time()}}
        elif stream["id"] not in fetched[stream["channel"]["name"]].keys():
            fetched[stream["channel"]["name"]][stream["id"]] = {
                                                  'downloaded': 'false',
                                                  'notified': 'false',
                                                  'timestamp': time.time()}
        try:
            if WEBHOOK_URL is not None and fetched[stream["channel"]["name"]][stream["id"]]["notified"] != 'true':
                notify(streamer_name, stream_id)
                fetched[stream["channel"]["name"]][stream["id"]]["notified"] = 'true'
        except KeyError:
            notify(streamer_name, stream_id)
            fetched[stream["channel"]["name"]][stream["id"]]["notified"] = 'true'
    save()
    # Get video_id's that have not been downloaded
    download_id = []
    for link in fetched:
        for id in fetched[link].keys():
            if fetched[link][id]['downloaded'] == 'false':
                download_id.append((link, id))
    # Download the not downloaded member video if there are videos to download
    if len(download_id) != 0:
        logger.debug(download_id)
        download_result = live_download.download(download_id)

        for stream_tuple in download_id:
            streamer = stream_tuple[0]
            stream_id = stream_tuple[1]
            logger.info(f"{streamer} is streaming, downloading {stream_id}")

        for downloaded in download_result:
            channel_name = downloaded[0]
            result_value = downloaded[1]
            for download_tuple in download_id:
                # download_tuple = ("channel_name", "channel_id")
                if channel_name in download_tuple[0]:
                    # set fetched video's downloaded key to download's key
                    stream_id = download_tuple[1]
                    fetched[channel_name][stream_id]['downloaded'] = result_value
        save()
    else:
        # TODO maybe put statement before log
        logger.info("No member's only stream found/downloaded")
        # print(" " * 40, end="\n")
        save()


def sleeping_text():
    counter = sleep_time
    print(" "*35, end="\n")
    while True:
        loading_string = f"[INFO] Sleeping for {counter} secs"
        if counter == 0:
            break
        print(loading_string, end="\r")
        counter -= 1
        time.sleep(1)


if __name__ == '__main__':
    logger.info("Starting Program")
    clear_link()
    expire_time = const.EXPIRE_TIME
    sleep_time = const.SLEEP_TIME
    cleared = True
    while True:
        try:
            if cleared:
                start_time = time.time()
                cleared = False
            if time.time() - start_time > expire_time:
                clear_link()
                start_time = time.time()
                cleared = True
            download()
            sleeping_text()
        except KeyboardInterrupt as k:
            logger.error(k)
            # print(" " * 40, end="\n")
        except Exception as e:
            logger.error(e, exc_info=True)
            # print(" " * 40, end="\n")
            logger.debug(fetched)
