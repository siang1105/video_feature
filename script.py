import youtube_dl
import csv
import argparse

csv_file = 'anet_video.csv'  # CSV 檔案路徑
output_file = 'sample/sample_video_paths.txt'  # 請替換為你要輸出的檔案路徑

def get_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument("id")
    args = parser.parse_args()
    return args

def download_youtube_video(url, video_id):
    ydl_opts = {
        'format': 'bestvideo/best',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'outtmpl': 'video/'+ video_id + '.%(ext)s', 
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

id = int((get_arg()).id)

with open(csv_file, 'r') as file, open(output_file, 'w') as output:
    video_id = file.readlines()[id].split(",")[0]
    output.write("/home/u4434246/siang/video_features/video/" + video_id + ".mp4\n")
    video_url = "https://www.youtube.com/watch?v=" + str(video_id)
    download_youtube_video(video_url, video_id)


