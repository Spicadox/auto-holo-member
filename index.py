import time
import json
import os
import urllib
import youtube_dl
from member_link import member_links
import log
import live_download
import requests
import re
import const

WEBHOOK_URL = const.WEBHOOK_URL
if const.LOGGING:
    logger = log.create_logger("logfile.log")
try:
    with open('channels.json', 'r', encoding="utf8") as f:
        channels = json.load(f)
except json.JSONDecodeError as jsonError:
    logger.error(jsonError)
    channels = {}
except ValueError as valuerror:
    logger.error(valuerror)
    channels = {}
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
            logger.info(f"Expired, Removing {link}")
            del fetched_json[link]

    # Saving json if links can be removed
    if len(removal) > 0:
        with open(FETCHED_JSON, "w", encoding="utf8") as writeFile:
            json.dump(fetched_json, writeFile, indent=4, ensure_ascii=False)
            logger.info("Saving json")


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
    logger.info("Getting member streams using yt_dl...")
    dict_list = []
    ytdl_format_options = {
        "playlistend": 1,
        "ignoreerrors": True,
        "logger": logger,
        "quiet": True,
        "no_warnings": True,
        "cookiefile": const.COOKIE
    }
    with youtube_dl.YoutubeDL(ytdl_format_options) as ytdl:
        for channel in channels.values():
            try:
                member_url = f"https://www.youtube.com/channel/{channel}/membership"
                logger.debug(member_url)
                info_dict = ytdl.extract_info(member_url, download=False)
                #logger.debug(info_dict)

                if info_dict is None:
                    continue

                try:
                    if info_dict['entries'][0]['is_live']:
                        dict_list.append({"id": info_dict['entries'][0]['id'], "title": info_dict['entries'][0]['title'],
                                          "channel": {"name": info_dict['entries'][0]['uploader']}})
                    else:
                        continue
                except Exception as e:
                    logger.debug(e)
                    continue
                time.sleep(4)
            except Exception as e:
                logger.error(e)
                continue
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
        url = f"https://youtu.be/{id}"
        message = f"{name} has a member-only stream live at {url}"
        requests.post(WEBHOOK_URL, json={'content': message})
    except Exception as e:
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
        logger.error(e)
        return False


def download():
    streams = get_links()
    for stream in streams:
        streamer_name = stream["channel"]["name"]
        stream_id = stream["id"]
        if stream["channel"]["name"] not in fetched.keys():
            fetched[stream["channel"]["name"]] = {'id': stream["id"],
                                                  'downloaded': 'false',
                                                  'notified': 'false',
                                                  'timestamp': time.time()}
            print(fetched)
            if WEBHOOK_URL is not None and fetched[stream["channel"]["name"]]["notified"] != 'true':
                notify(streamer_name, stream_id)
                fetched[stream["channel"]["name"]]['notified'] = 'true'
    save()
    # Get video_id's that have not been downloaded
    download_id = []
    for link in fetched:
        if fetched[link]['downloaded'] == 'false':
            download_id.append((link, fetched[link]["id"]))
    # Download the not downloaded member video if there are videos to download
    if len(download_id) != 0:
        download_result = live_download.download(download_id)
        streamer = download_id[0][0]
        stream_id = download_id[0][1]
        logger.info(f"{streamer} is streaming, downloading {stream_id}")

        for downloaded in download_result:
            # ("channel_name", "true")
            channel_name = downloaded[0]
            result_value = downloaded[1]
            for download_tuple in download_id:
                # download_tuple = ("channel_name", "channel_id")
                if channel_name in download_tuple[0]:
                    # set fetched video's downloaded key to download's key
                    fetched[channel_name]['downloaded'] = result_value
        save()
    else:
        logger.info("No member's only stream found/downloaded")
        save()


if __name__ == '__main__':
    logger.info("Starting Program")
    clear_link()
    expire_time = const.EXPIRE_TIME
    sleep_time = const.SLEEP_TIME
    while True:
        try:
            start_time = time.time()
            if time.time() - start_time > expire_time:
                clear_link()
                start_time = time.time()
            download()
            # change sleep time to 1 min maybe
            logger.info(f"Sleeping for {sleep_time} seconds\n")
            time.sleep(sleep_time)
        except KeyboardInterrupt as k:
            logger.error(k)
