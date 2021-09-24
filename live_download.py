import subprocess

setDownloaded = {}
def download(video_id):
    for video in video_id:
        # /c - close console after execution
        command_list = ['start', 'cmd', '/c']
        command_list += ['ytarchive.py', '--cookies', 'I:\\archive scripts\\batch scripts\\member_script\\newcookiefile_2.txt', '-o',
                         "NoArchive\%(channel)s\%(upload_date)s - %(title)s\%(upload_date)s - %(title)s (%(id)s)",
                         '--add-metadata', '-t', '--vp9', '--write-description', '--write-thumbnail', '--threads', '2',
                         '-w']
        command_list += [video]
        # remove later test line vvvvv
        # command_list += ['yt-dlp', '--cookies', 'I:\\archive scripts\\batch scripts\\member_script\\newcookiefile_2.txt', video]
        try:
            print("[INFO] Downloading Live Stream")
            output = subprocess.run(command_list, shell=True)
            # If theres an error then this ensures a redownload, but only works if the program crashes by itself immediately
            # print("[Debug] Output: ", output)
            print("[Debug] Immediate Return Code:", output.returncode)
            if output.returncode != 0:
                setDownloaded[video] = "false"
            setDownloaded[video] = "true"
        except Exception as e:
            print(e)
            setDownloaded[video] = "false"
    return setDownloaded

