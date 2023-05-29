#!/bin/sh

python main.py feature_type=clip device="cuda:$1" video_paths="[$HOME/repo/video_feature/video/v__$2.mp4]" extraction_fps=5 > $3/v__$2.log 2>&1

# python main.py feature_type=clip device="cuda:0" video_paths="[$HOME/repo/video_feature/video/v__C7sabT8febk.mp4]" extraction_fps=5 > log/test.log 2>&1