import os
import subprocess

def download(files):
    print(files)
    #Maybe only get the last file since its the most recent?
    for file in files:
        if '.json' in file:
            print("Found ", file)

            command_list = ['start', 'cmd', '/k']
            command_list += ["ytarchive-raw.py", '-t', '6', '-d', '-i', file]

            try:
                print("[INFO] Downloading Video")
                output = subprocess.run(command_list, shell=True)
                # If theres an error then this ensures a redownload, but only works if the program crashes by itself immediately
                # print("[Debug] Output: ", output)
                print("[Debug] Immediate Return Code:", output.returncode)
            except Exception as e:
                print(e)
                print("[INFO] Retry Download")
                output = subprocess.run(command_list)

