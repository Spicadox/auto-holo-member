import subprocess

setDownloaded = {}
DOWNLOAD = "/media/merged/NoArchive/%(channel)s/%(upload_date)s - %(title)s/%(upload_date)s - %(title)s (%(id)s)"
def download(video_id):
    for video in video_id:
        setDownloaded = False
        command_list = ['lxterminal', '-e', 'python3']
        command_list += ['ytarchive.py', '-o', DOWNLOAD,
                         '--add-metadata', '-t', '--ipv6', '--vp9', '--write-description', '--write-thumbnail', '--threads', '1',
                         '-w']
        command_list += [video, 'best']
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
