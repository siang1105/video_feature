import subprocess
import youtube_dl
import argparse
import threading
import time
from termcolor import colored
import os

csv_file = 'anet_video.csv'

LOGFOLDER = os.path.join("log", time.strftime("%Y-%m-%d", time.localtime()))

def get_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument("n", type=int, default=4, help="number of videos to download")
    args = parser.parse_args()
    return args

def extractFeature(ydl, urls, cuda, video_id, results, i):
    if video_id == "":
        results[i] = None
        return
    try: 
        ydl.download(urls)
        print(colored(f"Extracting Feature, video_id: {video_id}, cuda: {cuda}", "black", "on_cyan"))
        subprocess.Popen(["./video.sh", str(cuda), video_id, LOGFOLDER], stdout=subprocess.PIPE).wait()
        subprocess.Popen(["rm", "video/v__" + video_id + ".mp4"], stdout=subprocess.PIPE).wait()
        results[i] = f"{video_id},Done\n"
        print(colored(f"DONE: {video_id}", "green"))

    except Exception:
        print(colored(f"Error: {video_id}", "red"))
        subprocess.Popen(["rm", "video/v__" + video_id + ".mp4.part"], stdout=subprocess.PIPE).wait()
        results[i] = f"{video_id},Error\n"


if __name__ == '__main__':
    os.makedirs(LOGFOLDER, exist_ok=True)
    
    # n = get_arg().n

    n = sum(1 for line in open(csv_file, 'r'))

    ydl_opts = {
        'format': 'bestvideo/best',
        'outtmpl': 'video/v__%(id)s.%(ext)s', 
        'quiet': False,
        'no_warnings': True,
    }
    ydl = youtube_dl.YoutubeDL(ydl_opts)
    with open(csv_file, 'r') as file, open("log.txt", "a+") as log:
        log.write("-" * 20 + "\n")
        log.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n")
        
        num_of_success, num_of_error = 0, 0
        results = [None] * n
        for i in range(0, n, 4):
            video_ids = []
            processes = []
            threads = []
            
            j = 0
            for j in range(4):
                line = file.readline()
                if line == "":
                    break
                video_id = line.split(",")[0]
                video_url = "https://www.youtube.com/watch?v=" + str(video_id)
                video_ids.append(video_id)
                threads.append(threading.Thread(target = extractFeature, args = (ydl, [video_url], j, video_id, results, i+j)))

            for k in range(j):
                threads[k].start()
            
            for k in range(j):
                threads[k].join()
                if results[i+k] != None:
                    log.write(results[i+k])
                    if "Error" in results[i+k]:
                        num_of_error += 1
                    else:
                        num_of_success += 1

        print(colored(f"Success: {num_of_success}", "green"))
        print(colored(f"Error: {num_of_error}", "red"))
        log.write("All Done\n")
        log.write(f"Success: {num_of_success}, Error: {num_of_error}\n")


        
