
# coding: utf-8

# In[12]:


#!/Applications/sequence_analysis/anaconda3/bin/python



#### Import packages ####

from datetime import datetime
startTime = datetime.now()
from datetime import timedelta
import pandas as pd
import os
import sys
import subprocess
from subprocess import call
import ffmpy
from ffmpy import FFprobe
import json
import argparse
from pathlib import Path




#### Parse input arguments ####

Parser = argparse.ArgumentParser(description='Extract frames from Video')

Parser.add_argument('InputPath', 
                    action = 'store', 
                    nargs=1,
                    help = 'path to input directory')
Parser.add_argument('-o', 
                    action = 'store', 
                    nargs='?',
                    dest = 'OutputPath',
                    const = 'value-to-store',
                    help = '[optional] path to output directory (default: output_directory = input_directory)')
Parser.add_argument('-f', 
                    action = 'store',
                    nargs='?',
                    dest = 'OutputFramerate',
                    default = 1,
                    type = int,
                    help = '[optional] set output frame-rate/second. E.g. set "0.5" for one picture per two seconds (default: 1)')
Parser.add_argument('--jpg', 
                    action = 'store', 
                    default = 'PNG',
                    dest = 'ImageFormat',
                    help = '[optional] set JPG as output format (default: PNG)')
Parser.add_argument('--frameTimeLimit', 
                    action = 'store', 
                    default = False,
                    dest = 'FrameTimeLimit',
                    help = '[optional] Set time limit [sec] for frame extraction. E.g. set "20" for extracting frames only from the first 20 seconds')
Parser.add_argument('--removeOriginals', 
                    action = 'store_true', 
                    default = False,
                    dest = 'DeleteOriginalVideoFiles',
                    help = '[optional] CAUTION: if flag is set, all original video files will be removed after extracting frames (default: keep originals)')
Parser.add_argument('--logfile', 
                    action = 'store_true', 
                    default = False,
                    dest = 'ProduceLogfile',
                    help = '[optional] produce ExtractFramesFromVideo.log listing processed video files)')
Parser.add_argument('--jaguar', 
                    action = 'store_true', 
                    default = False,
                    dest = 'PrintJaguar',
                    help = ' ')


# parse input arguments
Args = Parser.parse_args()

#transfer arguments to variables
InputPath = str(Args.InputPath[0])
OutputPath = str(Args.OutputPath)
OutputFrameRate = Args.OutputFramerate
OutputFileExtension = Args.ImageFormat
PrintJaguar = Args.PrintJaguar
DeleteOriginalVideoFiles = Args.DeleteOriginalVideoFiles
ProduceLogfile = Args.ProduceLogfile
FrameTimeLimit = Args.FrameTimeLimit



# add max seconds

# working solution
####################################
#InputPath = "/Volumes/Fotos_1/CamTrapData_sorted_non-redundant/"
#OutputPath = "/Volumes/Fotos_1/CamTrapData_sorted_non-redundant/"
#OutputFrameRate = 2
#OutputFileExtension = "PNG"
#PrintJaguar = True
#DeleteOriginalVideoFiles = False
#ProduceLogfile = True
#FrameTimeLimit = 20
####################################

####################################
# define variables:
#OutputFrameRate = 1
#InputPath = "./" #this is still a problem
####################################



# needed for code:
metadata_creation_date = True

# Compile paths for log files:
if OutputPath:
    SkippedLogFileName = str(OutputPath+"/ExtractFramesFromVideo.skipped.log")
else:
    SkippedLogFileName = "ExtractFramesFromVideo.skipped.log"
if OutputPath:
    LogFileName = str(OutputPath+"/ExtractFramesFromVideo.log")
else:
    LogFileName = "ExtractFramesFromVideo.log"

# list of video file extensions to be supported here
VideoFileExtensions = (".avi", ".AVI", ".mov", ".MOV", ".mp4", ".MP4") # can be tested with other types and extended




#### Define Functions ####

'''
    For the given path, get the List of all video files in the directory tree 
'''
def getVideoFiles(directory):
    # create an initial list of files and sub directories,
    # at this point only in the specified directory (excluding 
    # files/directories in sub directories)
    list_of_files = os.listdir(directory)
    # create empty list that will later hold video files
    files = list()
    
    for entry in list_of_files:
        replaceChars = [' ','(',')']
        if any(item in entry for item in replaceChars):
        #if ' ' in entry or if '(' :
            def userPrompt():
                reply = str(input("\nUSER INPUT REQUIRED:\nWhite spaces and/or brackets found in paths inside "+InputPath+".\nFrames can only be extracted after replacing white spaces with underscores and removing brackets.\n\nType 'yes' to adjust file paths and continue.\nType 'no' to stop executing this script.\n\nUser input: ")).lower().strip()
                yes = ['Yes', 'Y', 'yes', 'y']
                no = ['No', 'N', 'no', 'n']
                if reply[0] in yes:
                    return True
                if reply[0] in no:
                    sys.exit("Execution stopped.\n")
                else:
                    print('Adjust file paths and names? Enter Yes/Y/yes/y or No/N/no/n.')
                    userPrompt()
            if userPrompt():
                replaceCommand = str('find '+InputPath+' -depth -name "* *" -o -name "*(*" -o -name "*)*" | while IFS= read -r f ; do mv -i "$f" "$(dirname "$f")/$(basename "$f" | tr "'" "'" _ | tr -d "'"()"'" )" ; done')
                subprocess.run(replaceCommand, shell=True)
                print('White spaces have been replaced with underscores.\n')
            new_list_of_files=[]
            for element in list_of_files:
                element = element.replace(' ','_').replace('(','').replace(')','')
                new_list_of_files.append(element)
            list_of_files = new_list_of_files
            break

    # Iterate over all the entries
    for entry in list_of_files:
        # Create full path
            full_path = os.path.join(directory, entry)
            # # extend file list to include nested directories
            if os.path.isdir(full_path):
                files = files + getVideoFiles(full_path)
            else:
                # now, that all files from all nested directories are considered, check,
                # if they are video files (= if they are in VideoFileExtensions)
                if entry.endswith(VideoFileExtensions):
                    # if so, add them to the final list of files to be returned
                    files.append(full_path)
                    
    return(files)


'''
    For any given file on a macOS file system return the file creation date [JJJJ-MM-DD hh:mm:ss]
    Doesn't work on Linux file systems, which don't support creation time
'''


def extractCreationDate_Attribute(in_file):
    # return list of stats from file system
    stat = os.stat(in_file)
    # extract creation date and transform it to a human readable format
    human_readable_date = datetime.fromtimestamp(stat.st_birthtime).strftime('%Y-%m-%d %H:%M:%S')
    human_readable_date = human_readable_date.replace(' ','_')
    
    return(human_readable_date)


'''
    For any video file ( at least MP4/AVI, others not yet tested) return a dictionary with metadata:
    file creation date (codec, duration [s], width [px], height [px], average frame rate (frames/s), 
    creation date [JJJJ-MM-DD hh:mm:ss], 
'''
def extractMetadata(in_file):
    # extract codec, duratiom, width, height, frame rate and if present the creation date from the video stream 
    # (-select_stream v) and pipe it to stdout in json format, decode it and safe it in intermediateDict
    ffp = ffmpy.FFprobe(
        inputs={in_file: None},
        global_options=['-hide_banner','-loglevel fatal','-v', 'quiet', "-select_streams", "v", "-show_entries", 
                        "stream=codec_name,duration,width,height,avg_frame_rate,nb_frames:stream_tags=creation_time", 
                        '-print_format', 'json']
    ).run(stdout=subprocess.PIPE)
    intermediate_dict = json.loads(ffp[0].decode('utf-8'))
    
    # Apparently, if cameras (Bushnell) are turned off while filming this can result in duration=0.000000 and nb_frames=N/A
    # in the metadata resulting in the nb_frames key missing in intermediate_dict and a nonsense value for duration of 
    # 0.000000 Therefore, check here, if nb_key exists and if duration == 0.000000. If one of the two is the case, skip the
    # file and add initiate or append it to a list of not processed video files.
    
    if 'nb_frames' not in intermediate_dict['streams'][0] or int(float(intermediate_dict['streams'][0]['duration'])) == 0:
        return False

    
    # create final dictionary
    metadata_dict = {}
    
    # add entries
    metadata_dict['codec']=str(intermediate_dict['streams'][0]['codec_name'])
    metadata_dict['duration']=float(intermediate_dict['streams'][0]['duration'])
    metadata_dict['frames']=float(intermediate_dict['streams'][0]['nb_frames'])
    metadata_dict['width']=str(intermediate_dict['streams'][0]['width'])
    metadata_dict['height']=str(intermediate_dict['streams'][0]['height'])
    metadata_dict["creation_time_attribute"]=extractCreationDate_Attribute(in_file) # creation time  from the file system
    
    # reformat creation time to match 'JJJJ-MM-DD hh:mm:ss'
    try:
        tmp_creation_time = str(intermediate_dict['streams'][0]['tags']['creation_time'])
        tmp_date = tmp_creation_time[:10]
        tmp_time = tmp_creation_time[11:19]
        tmp_creation_time = str(tmp_date+"_"+tmp_time)
        metadata_dict['creation_time_metadata']=tmp_creation_time
    except:
        metadata_creation_date = False
        pass
        
    # reformat frame rate if necessary
    tmp_frame_rate = str(intermediate_dict['streams'][0]['avg_frame_rate'])
    tmp_frame_rate = tmp_frame_rate.split("/")
    tmp_frame_rate =[ int(x) for x in tmp_frame_rate ]
    tmp_frame_rate = tmp_frame_rate[0]/tmp_frame_rate[1]
    tmp_frame_rate = str(tmp_frame_rate)+"/1"
    metadata_dict['frame_rate']=tmp_frame_rate
    
    return(metadata_dict)


'''
    Given a video file compile a list of frames to be extracted
'''
###### old version
#def compileExportFrameList(frames, duration, output_frame_rate, frame_time_limit):
#    frame_list = []
#    frame_list.append(int(1)) # always export first frame with highest probability of sighting
#    input_frame_rate = float(frames)/float(duration)
#    num_output_frames = int(float(duration)/float(output_frame_rate))
#    if frame_time_limit not None:
#        lock_output_frames = int(float(output_frame_rate)*float(frame_time_limit))
#        if lock_output_frames < num_output_frames:
#            num_output_frames = lock_output_frames
#        else:
#            pass
#    for i in range(1,(num_output_frames+1),output_frame_rate):
#        frame_time = round(i*input_frame_rate)
#        frame_list.append(frame_time)
#        
#    return(frame_list)

def compileExportFrameList(frames, duration, output_frame_rate, frame_time_limit):
    frame_list = []
    reciprocal_output_frame_rate = 1/output_frame_rate
    input_frame_rate = float(frames)/float(duration)
    num_output_frames = int((float(duration)/float(reciprocal_output_frame_rate))/output_frame_rate)
    if frame_time_limit:
        lock_output_frames = int((float(output_frame_rate)*float(frame_time_limit))/output_frame_rate)
        if lock_output_frames < num_output_frames:
            num_output_frames = lock_output_frames
        else:
            pass
    for i in list([x / 10.0 for x in range(0, int((num_output_frames*10)), int(reciprocal_output_frame_rate*10))]):


        frame_time = round(i*(input_frame_rate))

        frame_list.append(frame_time)
    frame_list[0]=1 # always extract first frame
    
    return(frame_list)
    
    
    
'''
    Compile a filename 
'''
def compileOutFileName(frame, video_file_name, file_extension):
    try:
        out_file_name = str(video_file_name+"_"+(Metadata['creation_time_metadata']).replace(':','-')+'_frame_'
                          +str(frame)+'.'+file_extension)
    except:
        out_file_name = str(video_file_name+"_"+(Metadata['creation_time_attribute']).replace(':','-')+'_frame_'
                          +str(frame)+'.'+file_extension)
        
    return(out_file_name) 


'''
    Extract video frames by number
'''
def extractFrames(in_file, out_file_name, frame):
    bash_command = str('ffmpeg -y ' + '-hide_banner ' + '-loglevel fatal ' + '-i '+ in_file + ' -vf "select=gte(n\,'+ str(frame)+ ')" -vframes 1 '
                       +out_file_name)
    call(bash_command, shell=True)

    
'''
    Edit exif data (add creation date and original video file name)
'''
def writeExif(file_name, date_time, original_file_name):
    creation_date = date_time.replace('-',':').replace('_',' ')
    bash_command = str('exiftool -quiet -DateTimeOriginal="' + creation_date + '" -OriginalFilename="'
                       +original_file_name+'" -overwrite_original '+ file_name)
    call(bash_command, shell=True)

'''
    Modify creation- and modification date in extracted frame file file to match original video file
'''
def setTimeStamp(date_string, in_file):
    date_string = date_string.replace(':','_').replace('-','_').split('_')
    date_list = [int(i) for i in date_string]
    datetime_date = datetime(date_list[0], date_list[1], date_list[2], date_list[3], date_list[4], date_list[5])
    os.system('SetFile -d "{}" {}'.format(datetime_date.strftime('%m/%d/%Y %H:%M:%S'), in_file))
    os.system('SetFile -m "{}" {}'.format(datetime_date.strftime('%m/%d/%Y %H:%M:%S'), in_file))
    
    
#### Los gehts ####
    
if PrintJaguar == True:
    print('')
    print('       ▕▔▔╲╱▋▔▋▔▋╲╱▔▔▏')
    print('       ▕┈▔╲▍┈▋┈▍┈▋╱▔┈▏')
    print('        ╲╱┳▅╮┊┊┊╭▅┳╲╱ ')
    print('        ▕▋╰━┫┊┊┊┣━╯▋▏ ')
    print('         ╲▍╱┈▂▂▂┈╲▍╱  ')
    print('          ╲▏┈╲▂╱┈▕╱   ')
    print('           ╲▂╱▔╲▂╱    ')
    print('            ╲▂▂▂╱     ')
    print('')
    

# compile a list of all video files located within the specified directory including subdirectories
FileList = getVideoFiles(InputPath)

# from FileList compile a dictionary that holds two values per element: path (excluding filename) and 
# filename (excluding path)
FileDict = {}

# iterate FileList
for Element in FileList:
    # split at each '/'
    Levels = Element.split('/')
    # count number of Elements, the last one is the filename
    NLevels=len(Levels)
    # by index extract filename from Elements
    FileName = Levels[(NLevels)-1]
    # filepath is the whole path - filename
    FilePath = Element.strip(FileName)
    # for each Element(=filepath+filename) add a nested dictionary holding filename + filepath
    FileDict[Element] = {}
    FileDict[Element]["filename"] = FileName
    FileDict[Element]["filepath"] = FilePath


# iterate through FileList
for File in FileList:
    
    VideoFileName = FileDict[File]["filename"]

    # extract Metadata from video file and file system
    try:
        Metadata = extractMetadata(File)
    except:
        Metadata =  False
    
    # check if there is a problem with nb_frames or duration (see def extractMetadata):
    if Metadata == False:
        print("ERROR: Metadata truncated of file corrupted: " + File + ". File will be skipped and added to ExtractFramesFromVideo.skipped.log.")
        
        # append file path to ExtractFramesFromVideo.skipped.log
        try:
            with open(SkippedLogFileName,"a+") as skippedLogfile:
                skippedLogfile.write(str(File + "\n"))
                continue
        # a+ can create outputfiles but not missing directories... So if missing, create output directory first 
        except:
            os.makedirs(OutputPath, exist_ok=True)
            with open(SkippedLogFileName,"a+") as skippedLogfile:
                skippedLogfile.write(str(File + "\n"))
                continue
                
    Frames = float(Metadata['frames'])
    Duration = float(Metadata['duration'])
    
    # check if EXIF file contains a creation date
    try: 
        CreationTime=(Metadata['creation_time_metadata'])
        
    # if not use file system creation date instead
    except:
        CreationTime=(Metadata['creation_time_attribute'])
    
    # compile a list of frames to be extracted
    FrameList = compileExportFrameList(Frames, Duration, OutputFrameRate, FrameTimeLimit)
    
    # iterate frames in frame list 
    for ExportFrame in FrameList:       

        OutfileName =  str(compileOutFileName(ExportFrame, VideoFileName, OutputFileExtension))

         #check if outputfile was set:
        if not OutputPath:
            # compile output file path (including filename)
            OutfilePath = str("."+str(FileDict[File]["filepath"]))
            
             # extract a frame
            extractFrames(File, OutfilePath, ExportFrame)

            # tweak EXIF data to match craetion date + time in tag "DateTimeOriginal" and 
            # to indlude the name of the source video file in the tag "OriginalFileName"
            writeExif(OutfilePath, CreationTime, VideoFileName)
            # also change the time stamp to show the original creation- and modification date:
            setTimeStamp(CreationTime, OutfilePath)
        
        #check if outputfile was set:
        if OutputPath:
            OutfilePath = str(OutputPath+str(FileDict[File]["filepath"])
                          + OutfileName)
            
            # check if specified output directory exists
            if (os.path.isfile(OutfilePath)) is True:
                pass
            
            # else: create it
            if (os.path.isfile(OutfilePath)) is False:
                os.makedirs('/'.join(OutfilePath.split('/')[:-1]), exist_ok=True)

            # extract a frame
            extractFrames(File, OutfilePath, ExportFrame)

            # tweak EXIF data to match craetion date + time in tag "DateTimeOriginal" and 
            # to indlude the name of the source video file in the tag "OriginalFileName"
            writeExif(OutfilePath, CreationTime, VideoFileName)
            # also change the time stamp to show the original creation- and modification date:
            setTimeStamp(CreationTime, OutfilePath)
    
    # if '--logfile' is set: 
    if ProduceLogfile is True:
        with open(LogFileName,"a+") as logfile:
            logfile.write(str(File + "\n"))
        
    # if '--removeOriginals' specified, remove original videofile
    if DeleteOriginalVideoFiles is True:
        os.remove(File)

        
# compile and print startTime, endTime and runTime:
endTime = datetime.now()
runTime = endTime - startTime
runTimeDays = runTime.days
runTimeSeconds = int(runTime.seconds)

print('\n')
print('done')
print('\n')
print('start time: '+"\t"+"\t"+str(startTime)[:-7])
print('end time: '+"\t"+"\t"+str(endTime)[:-7])
print('\n')
print('total run time: '+"\t"+str(timedelta(seconds=runTimeSeconds)))
print('\n')


# In[ ]:




