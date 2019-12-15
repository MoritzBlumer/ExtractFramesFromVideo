# Script to extract frames from videos in bulk

## Motivation:

Provided a mixed dataset of image and video files in a nested directory structure, we looked for a way to extract a fixed number of frames for the first 10 seconds from each video file. This script uses [FFmpeg](https://www.ffmpeg.org) to extract frames and uses [ExifTool](https://exiftool.org) to read datetime information from the original video file and to write it to the meta data of the extracted frames. The user can set the rate at which frames will be extracted [-f] and a time limit in seconds after which extraction of files stops [--frameTimeLimit]. If no output [-o] directory is specified, frames will be extracted in place. If extraction fails for any video file, it will be added to an error log file. 



## Dependencies:
* Python 3
* [ffmpy](https://pypi.org/project/ffmpy/)		(pip install ffmpy)
* [exiftool](https://exiftool.org)		(callable from command line)
* python packages (standard library): pandas, datetime, os, sys, subprocess, json, argparse, pathlib


## Usage:

ExtractFramesFromVideo.py InputPath [optional parameters]


### Optional parameters:

------------------ | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
-h                 | display help message |                                                                                                                                     |
-o, --outputpath   | output path          | set path to output directory (default: output_directory = input_directory)                                                          |
-f, --framerate    | frame rate           | set output frame-rate/second. E.g. set "0.5" for one picture per two seconds (default: 1)                                           |
--frameTimeLimit   | frame time limit     | set time limit [sec] for frame extraction (e.g. set "20" to extract extracting frames from the first 20 seconds (default: no limit) |
--removeOriginals  | remove originals     | CAUTION: if flag is set, all original video files will be removed after extracting frames (default: keep originals)                 |
--logfile          | generate logfile     | produce "ExtractFramesFromVideo.log" listing processed video files                                                                  |
--jpg              | JPG                  | set JPG as output format (default: PNG)                                                                                             |



## Example:

ExtractFramesFromVideo.py inputPath -o outputPath -f 2 --frameTimeLimit 10 --removeOriginals --logfile

This would generate a copy of the inputPath directory structure at outputPath and extract 2 images per second for the first 10 seconds of every video present in inputPath and all subdirectories (-->  20 frames (PNG) per video file).
