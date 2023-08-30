import re
import subprocess
import numpy as np
import youtube_dl
import threading
import time
from termcolor import colored
import os
import glob
from omegaconf import OmegaConf
from utils.utils import build_cfg_path

def checkFileExist(video_id):
    return os.path.isfile(os.path.join(config.output_path, config.feature_type, config.model_name, "v_" + video_id + "_" + config.feature_type + ".npy"))

def validFeature(video_id):
    try:
        data = np.load(os.path.join(config.output_path, config.feature_type, config.model_name, "v_" + video_id + "_" + config.feature_type + ".npy"))
        if isinstance(data, np.ndarray) and data.size > 0:
            return True
    except Exception:
        return False
    return False

def extractFeature(ydl, urls, cuda, video_id, results, i, config):
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
                pass

        ydl.download(urls)
        print(colored(f"Extracting Feature, video_id: {video_id}, cuda: {cuda}", "black", "on_cyan"))

        with open(os.path.join(config.log_folder, "v_" + video_id + ".log"), "w+") as log:
            subprocess.Popen(["python", "main.py",
                              f"device=cuda:{cuda}", 
                              f"feature_type={config.feature_type}", 
                              f"on_extraction={config.on_extraction}", 
                              f"video_paths=[{config.tmp_path}/video/v_{video_id}.mp4]",
                              f"tmp_path={config.tmp_path}",
                              f"extraction_fps={config.extraction_fps}", 
                              f"output_path={config.output_path}"
                            ], stdout=log, stderr=log).wait()
        
        results[i] = f"{video_id},Done\n"
        print(colored(f"DONE: {video_id}", "green"))
    except Exception as e:
        # Error: 1. Video not found 2. Video is private 3. Video is deleted
        errorMsg = re.sub('\033\[.*?m', '', str(e)).split("ERROR:")[1].strip().split("\n")[0]
        results[i] = f"{video_id},Error,{errorMsg}\n"
    
    files = glob.glob(os.path.join(f"{config.tmp_path}/video", "v_" + video_id + "*"))
    if len(files) > 0:
        subprocess.Popen(["rm"] + files, stdout=subprocess.PIPE).wait()

def handle_config(args_cli):
    # Load config
    # Priority: args_cli > config2 > config1
    config = OmegaConf.load("./configs/extract_feature.yml")
    config = OmegaConf.merge(config, args_cli)
    model_config = OmegaConf.load(build_cfg_path(config.feature_type))
    config = OmegaConf.merge(model_config, config)
    
    if(config.reverse) :
        config.log_folder = os.path.join("log", config.feature_type, time.strftime("%Y-%m-%d", time.localtime()) + "-reverse")
        config.log_file = os.path.join("log", config.feature_type, config.feature_type + "-" + time.strftime("%Y-%m-%d", time.localtime()) + "-reverse.log")
    else :
        config.log_folder = os.path.join("log", config.feature_type, time.strftime("%Y-%m-%d", time.localtime()))
        config.log_file = os.path.join("log", config.feature_type, config.feature_type + "-" + time.strftime("%Y-%m-%d", time.localtime()) + ".log")

    return config

if __name__ == '__main__':
    # Load config
    args_cli = OmegaConf.from_cli()
    config = handle_config(args_cli)
    # print(config)

    # Prepare youtube-dl
    ydl_opts = {
        'format': 'bestvideo/best',
        'outtmpl': f'{config.tmp_path}/video/v_%(id)s.%(ext)s', 
        'quiet': False,
        'no_warnings': True,
        'format': 'bestvideo[ext=mp4]/mp4',
        'quiet': False,
    }
    ydl = youtube_dl.YoutubeDL(ydl_opts)


    # Read video list
    video_list = []
    with open(config.video_list, 'r') as file:
        for line in file:
            video_list.append(line.split(",")[0])
    if config.reverse:
        video_list.reverse()
    n = len(video_list)
    results = [None] * n

    # Start extracting
    print(colored(f"Extracting {n-config.skip} videos", "blue"))
    print(colored(f"Using {config.num_of_device} GPUs", "blue"))
    
    # Create log folder and write datetime to log file
    os.makedirs(config.log_folder, exist_ok=True)
    with open(config.log_file, "a+") as log:
        log.write("-" * 20 + "\n")
        log.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n")
    
    num_of_success, num_of_error = 0, 0
    for i in range(config.skip, n, config.num_of_device):
        threads = []
    
        for j in range(config.num_of_device):
            if i+j >= n:
                break
            video_id = video_list[i+j].split(",")[0]
            video_url = "https://www.youtube.com/watch?v=" + str(video_id)
            threads.append(threading.Thread(target = extractFeature, args = (ydl, [video_url], j, video_id, results, i+j, config)))

        for thread in threads:
            thread.start()
        
        for k, thread in enumerate(threads):
            thread.join()
            if results[i+k] != None:
                with open(config.log_file, "a+") as log:
                    log.write(str(i+k) + ',' + results[i+k])
                if "Error" in results[i+k]:
                    num_of_error += 1
                else:
                    num_of_success += 1


    print(colored(f"Success: {num_of_success}", "green"))
    print(colored(f"Error: {num_of_error}", "red"))
    with open(config.log_file, "a+") as log:
        log.write("All Done\n")
        log.write(f"Success: {num_of_success}, Error: {num_of_error}\n")

