import subprocess
import const

setDownloaded = []


def download(videos):
    for video in videos:
        channel_name = video[0]
        video_id = video[1]
        # /c - close console after execution
        command_list = ['start', 'cmd', '/c']
        command_list += ['ytarchive.exe', '--cookies', const.COOKIE, '-o',
                         const.DOWNLOAD,
                         '--add-metadata', '-t', '--vp9', '--write-description', '--write-thumbnail', '--threads', '2',
                         '-w']
        command_list += [f'https://www.youtube.com/watch?v={video_id}', 'best']
        # remove later test line
        # command_list += ['yt-dlp', '--cookies', 'I:\\archive scripts\\batch scripts\\member_script\\newcookiefile_2.txt', video]
        try:
            output = subprocess.run(command_list, shell=True)
            # If theres an error then this ensures a redownload, but only works if the program crashes by itself immediately
            # print("[Debug] Output: ", output)
            if output.returncode != 0:
                setDownloaded.append((channel_name, "false"))
            setDownloaded.append((channel_name, "true"))
        except Exception as e:
            print(e)
            setDownloaded.append((channel_name, "false"))
    return setDownloaded

