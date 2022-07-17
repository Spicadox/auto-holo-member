import threading
import time
import json
import os
from requests.adapters import HTTPAdapter
import log
import live_download
import requests
import re
import const
import yt_dlp


WEBHOOK_URL = const.WEBHOOK_URL
DEAD_MEMBER_WEBHOOK_URL = const.DEAD_MEMBER_WEBHOOK_URL

if const.LOGGING:
    logger = log.create_logger("logfile.log")
    ytdlp_logger = log.YTLogger
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
                "status": "OK",
                "timestamp": 1652023702.6788592
            }
    }
}
"""


def save():
    with open(FETCHED_JSON, "w", encoding="utf8") as writeFile:
        json.dump(fetched, writeFile, indent=4, ensure_ascii=False)


def clear_link(expire_time):
    with open(FETCHED_JSON, encoding="utf8") as readFile:
        fetched_json = json.load(readFile)

        removal = []
        for link in fetched_json.keys():
            for id in fetched_json[link].keys():
                if time.time() - fetched_json[link][id]['timestamp'] > expire_time:
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
            # logger.info("Saving json")


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
    ydl_opts = {"quiet": True, "no_warnings": True, "cookiesfrombrowser": ('chrome',), "playlistend": 1, "logger": ytdlp_logger}
    with yt_dlp.YoutubeDL(ydl_opts) as ydlp:
        for channel in channels.values():
            try:
                print(f"[INFO] Looking through member's pages {counter}/{dict_length}...", end="\r")

                info = ydlp.extract_info(f"https://www.youtube.com/channel/{channel}/membership", download=False)
                info_dict = ydlp.sanitize_info(info)
                if info_dict.get('entries')[0].get('is_live'):
                    dict_list.append({"id": info_dict['entries'][0]['id'], "title": info_dict['entries'][0]['title'],
                                      "channel": {"name": info_dict['channel'], 'id': channel}})
                else:
                    continue
            except json.JSONDecodeError as jsonError:
                logger.debug(str(jsonError) + f" occurred when looking through {channel}")
            except KeyError as kError:
                logger.debug(kError)
            except yt_dlp.utils.DownloadError as dError:
                logger.debug(dError)
            except Exception as e:
                logger.debug(str(e) + " "*50, exc_info=True)
            finally:
                counter += 1
    return dict_list


def notify(channel, id, session):
    try:
        channel_url = "https://www.youtube.com/channel/" + channel[1]
        url = f"https://youtu.be/{id}"
        message = f"[{channel[0]}](<{channel_url}>) has a member-only stream live at {url}"
        session.post(WEBHOOK_URL, json={'content': message})
    except requests.exceptions.HTTPError as hError:
        logger.error(hError, exc_info=True)
    except requests.exceptions.RequestException as rException:
        logger.error(rException, exc_info=True)
    except KeyError as kError:
        logger.error(kError)
        logger.debug(channels)
    except Exception as e:
        logger.error(e, exc_info=True)


def notify_dead(message, session):
    try:
        session.post(DEAD_MEMBER_WEBHOOK_URL, json={'content': message})
    except Exception as e:
        logger.error(e)


def download():
    streams = get_latest_member_streams()
    for stream in streams:
        streamer = (stream["channel"]["name"], stream["channel"]["id"])
        stream_id = stream["id"]
        try:
            import util
            url = f"https://youtu.be/{stream_id}"
            util.get_json(url)
        except (ImportError, ModuleNotFoundError):
            pass
        except Exception as e:
            logger.error(e)
        # TODO    Take a look and change if statement later
        if stream["channel"]["name"] not in fetched.keys():
            fetched[stream["channel"]["name"]] = {stream["id"]: {
                                                  'downloaded': 'false',
                                                  'notified': 'false',
                                                  'status': 'OK',
                                                  'timestamp': time.time()}}
        elif stream["id"] not in fetched[stream["channel"]["name"]].keys():
            fetched[stream["channel"]["name"]][stream["id"]] = {
                                                  'downloaded': 'false',
                                                  'notified': 'false',
                                                  'status': 'OK',
                                                  'timestamp': time.time()}
        try:
            if WEBHOOK_URL is not None and fetched[stream["channel"]["name"]][stream["id"]]["notified"] != 'true':
                notify(streamer, stream_id, session)
                fetched[stream["channel"]["name"]][stream["id"]]["notified"] = 'true'
        except KeyError:
            notify(streamer, stream_id, session)
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
        try:
            import util
            import threading
            if const.CHAT_PATH is not None:
                for d_id in download_id:
                    threading.Thread(target=util.get_chat, args=[d_id[1]]).start()
        except (ImportError, ModuleNotFoundError, NameError):
            pass
        except Exception as e:
            logger.error(e)
            pass
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
        logger.debug("No member's only stream found/downloaded")
        # print(" " * 40, end="\r")
        save()


def check_status(session):
    if len(fetched) != 0:
        global stop_loading
        stop_loading = False
        threading.Thread(target=loading_text).start()
        url = "https://www.youtube.com/watch?v="
        save_change = False
        for channel in fetched:
            for id in fetched[channel]:
                try:
                    res = session.get(url+id).text
                except requests.exceptions as reqExceptions:
                    logger.error(reqExceptions)
                    continue
                var = re.search(pattern="(var ytInitialPlayerResponse = )([^\n].*)", string=res)
                if var is not None:
                    res = var.group(2)
                status = ""
                copyright_message = ['copyright', 'copyrighted', 'Copyright', 'Copyrighted']
                if '"status":"UNPLAYABLE"' in res and any(message in res for message in copyright_message):
                    status = "Copyrighted"
                elif '"Private video"' in res:
                    status = "Privated"
                elif '"status":"ERROR"' in res:
                    status = "Removed"
                elif '"isUnlisted":true"' in res:
                    status = "Unlisted"

                if fetched[channel][id]["status"] == "OK" and status != "":
                    channel_url = "https://www.youtube.com/channel/" + channels[channel]
                    url = f"https://youtu.be/{id}"
                    message = f"Member-only stream from [{channel}](<{channel_url}>) is now `{status}` at {url}"
                    logger.info(message)
                    logger.debug(res[:3000])
                    fetched[channel][id]["status"] = status
                    save_change = True
                    if const.DEAD_MEMBER_WEBHOOK_URL != "":
                        notify_dead(message, session)
        if save_change:
            save()
        stop_loading = True


def sleeping_text():
    counter = sleep_time
    print(" "*70, end='\r')
    while True:
        loading_string = f"[INFO] Sleeping for {counter} secs..."
        if counter == 0:
            break
        print(loading_string, end="\r")
        counter -= 1
        time.sleep(1)


def loading_text():
    loading_string = "[INFO] Checking member's only stream status "
    animation = ["     ", ".    ", "..   ", "...  ", ".... ", "....."]
    idx = 0
    while not stop_loading:
        print(loading_string + animation[idx % len(animation)], end="\r")
        time.sleep(0.3)
        idx += 1
        if idx == 6:
            idx = 0


if __name__ == '__main__':
    logger.info("Starting Program")
    expire_time = const.EXPIRE_TIME
    sleep_time = const.SLEEP_TIME
    clear_link(expire_time)
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=5))
    while True:
        try:
            download()
            check_status(session)
            if len(fetched) != 0:
                clear_link(expire_time)
        except KeyboardInterrupt as k:
            logger.debug(k, exc_info=True)
        except Exception as e:
            logger.error(e, exc_info=True)
            logger.debug(fetched)
