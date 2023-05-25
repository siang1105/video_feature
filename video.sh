for i in {0..8..4}
do
    python script.py $i 
    videoPath=$(cat sample/sample_video_paths.txt)
    python main.py feature_type=clip device="cuda:0" video_paths="[${videoPath}]" extraction_fps=5
    rm ./video/*
done