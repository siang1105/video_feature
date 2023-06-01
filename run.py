import re
import subprocess
import numpy as np
import youtube_dl
import threading
import time
from termcolor import colored
import os
import glob
import torch

CSV_FILE = 'anet_video.csv'
LOGFOLDER = os.path.join("log", time.strftime("%Y-%m-%d", time.localtime()))
FEATUREPATH = "/home/u8637030/VLCAP/data/clip/ViT-B_32"
NUM_OF_DEVICE = torch.cuda.device_count()

def checkFileExist(video_id):
    return os.path.isfile(os.path.join(FEATUREPATH, "v__" + video_id + "_clip" + ".npy"))

def validFeature(video_id):
    try:
        data = np.load(os.path.join(FEATUREPATH, "v__" + video_id + "_clip" + ".npy"))
        if isinstance(data, np.ndarray) and data.size > 0:
            return True
    except Exception:
        return False
    return False

def extractFeature(ydl, urls, cuda, video_id, results, i):
    if video_id == "":
        results[i] = None
        return
    try: 
        if checkFileExist(video_id):
            if validFeature(video_id):
                results[i] = f"{video_id},Skip\n"
                print(colored(f"SKIP: {video_id}", "yellow"))
                return
            else:
                print(colored(f"Waring: Invalid Feature, video_id: {video_id}", "yellow"))

        ydl.download(urls)
        print(colored(f"Extracting Feature, video_id: {video_id}, cuda: {cuda}", "black", "on_cyan"))
        subprocess.Popen(["./video.sh", str(cuda), video_id, LOGFOLDER], stdout=subprocess.PIPE).wait()
        results[i] = f"{video_id},Done\n"
        print(colored(f"DONE: {video_id}", "green"))
    except Exception as e:
        # Error: 1. Video not found 2. Video is private 3. Video is deleted
        errorMsg = re.sub('\033\[.*?m', '', str(e)).split("ERROR:")[1].strip().split("\n")[0]
        results[i] = f"{video_id},Error,{errorMsg}\n"
    
    files = glob.glob(os.path.join("video", "v__" + video_id + ".*"))
    files += glob.glob(os.path.join("video", "v__" + video_id + ".webm.*"))
    files += glob.glob(os.path.join("video", "v__" + video_id + ".mp4.*"))
    if len(files) > 0:
        subprocess.Popen(["rm"] + files, stdout=subprocess.PIPE).wait()

if __name__ == '__main__':
    os.makedirs(LOGFOLDER, exist_ok=True)

    n = sum(1 for line in open(CSV_FILE, 'r'))

    ydl_opts = {
        'format': 'bestvideo/best',
        'outtmpl': 'video/v__%(id)s.%(ext)s', 
        'quiet': False,
        'no_warnings': True,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
    }
    ydl = youtube_dl.YoutubeDL(ydl_opts)
    with open(CSV_FILE, 'r') as file:
        with open("log.txt", "a+") as log:
            log.write("-" * 20 + "\n")
            log.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n")
        
        num_of_success, num_of_error = 0, 0
        results = [None] * n
        
        print(colored(f"Extracting {n} videos", "blue"))
        print(colored(f"Using {NUM_OF_DEVICE} GPUs", "blue"))

        for i in range(0, n, NUM_OF_DEVICE):
            threads = []
        
            for j in range(NUM_OF_DEVICE):
                line = file.readline()
                if line == "":
                    break
                video_id = line.split(",")[0]
                video_url = "https://www.youtube.com/watch?v=" + str(video_id)
                threads.append(threading.Thread(target = extractFeature, args = (ydl, [video_url], j, video_id, results, i+j)))

            for thread in threads:
                thread.start()
            
            for k, thread in enumerate(threads):
                thread.join()
                if results[i+k] != None:
                    with open("log.txt", "a+") as log:
                        log.write(results[i+k])
                    if "Error" in results[i+k]:
                        num_of_error += 1
                    else:
                        num_of_success += 1

        print(colored(f"Success: {num_of_success}", "green"))
        print(colored(f"Error: {num_of_error}", "red"))
        with open("log.txt", "a+") as log:
            log.write("All Done\n")
            log.write(f"Success: {num_of_success}, Error: {num_of_error}\n")


        
