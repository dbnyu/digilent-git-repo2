"""Wait for trigger pulses on Scope input and record timestamps of [this] host PC to file.


    Doug Brantner
    2/25/2022

    References:
    - https://docs.python.org/3/library/signal.html#signal.SIGINT
    - https://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
    - https://docs.python.org/3/tutorial/inputoutput.html
"""




from ctypes import *
from dwfconstants import *
import ad2_tools_basic as ad2b

import datetime
import argparse
import pathlib
import signal
import sys
import os



# TODO avoid Anaconda imports (numpy, pandas etc.) - works in Cygwin without them (so far)
# TODO loop forever
# TODO wait for trigger
# TODO record timestamp string
#   TODO - MATCH TOFCAMERA STRING FORMAT?
#   TODO - record raw (simplest/fastest representation) of timestamp & parse to human later?
# TODO write to file
#   TODO ramdisk/tmpfile? for faster writing?
#   TODO could lead to memory issues with other recordings ( TOF camera) or long acquisitions...
#   TODO may need to do some code profiling to make sure diskwrites are fast enough
#   TODO diagnostic function to troubleshoot?
# DONE catch Ctrl+C and end loop
# DONE? catch all exceptions and CLOSE THE FILE PROPERLY- then re-throw?
#       -failsafe so that data is not lost if there's some error...
#       - 'with' block should guarantee this...
# TODO indicator onscreen?
#   TODO on linux, can just tail/follow the output file, or 'tee'
#   TODO make this optional (ideally without 'if' statements) to display or not display full strings
#       NOTE screen I/O can be slow
#   TODO also just a 'period' to show that it's working...
#   TODO pulses are order of milliseconds... so every 1000th pulse shouldn't hurt too much
#       TODO look for delays that correlate with this just to be safe...
#   TODO [#C] could also blink an LED on the AD2... but that doesn't prove file is getting written.
# TODO - optimization - only get the TIME and not the full DATE/TIME, save some bits???
#   - only need to store the date once ie. in filename...
# TODO - could print some 'useful' information ie. approx. pulse frequency
#       - meaning rough pulses/sec frequency counter (which should match MRI TR)
#       - might require a circular buffer...
# TODO - optimization - is there a way to do C-like macros for options that may cause lag???
#       - ie. completely omit from code, rather than adding 'if' statements that are always false?
#       - TODO - does python compiler smartly skip 'if' statements that are always false????
#       - TODO - ie. if the value is never touched again, can it optimize out the whole branch???



# Parse Input Arguments
parser = argparse.ArgumentParser(description='Analog Discovery 2 - Trigger Timestamp Recorder')
parser.add_argument('-f', '--folder', required=True, help='directory to save files')
# TODO make default 'this' folder?
parser.add_argument('-d', '--desc',   default='timestamps', help='short description for filename')
#parser.add_argument('-p', '--pulseinfo', type=bool, default=False, help='append pulse info to filename')

args = parser.parse_args()
out_folder = args.folder
description = args.desc

startTime = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
filename = '%s_%s.csv' % (startTime, description)
#filename = '20220225-150808_timestamps.csv'    # test for if file already exists (timestamped names should avoid this anyway)

fullpath = os.path.join(out_folder, filename)


def close_file():
    # TODO  - this should be called by sigint handler AND global try/catch
    # TODO maybe we don't need this ('with' is supposedly guaranteed to close the file safely?)
    pass


def signal_handler(signal, frame):

    # TODO close file safely
    print('Exiting...')

    sys.exit(0) # TODO get return code from file closer?


# TODO setup AD2
# TODO START HERE


pathlib.Path(out_folder).mkdir(parents=True, exist_ok=True)

print('Saving timestamps in folder: %s' % out_folder)
print('Filename: %s' % filename)


# register signal handler (before/right after file is actually opened)
signal.signal(signal.SIGINT, signal_handler)    # TODO make sure this works cross-platform!
# works in Powershell (Windows 10 host/Anaconda)
# works in Cygwin (Windows 10 host/Anaconda python but no libraries/env)



# NOTE: 'with' block should close file safely even with an exception:
# "It is good practice to use the with keyword when dealing with file objects. 
# The advantage is that the file is properly closed after its suite finishes, 
# even if an exception is raised at some point. Using with is also much shorter than 
# writing equivalent try-finally blocks"
# - from https://docs.python.org/3/tutorial/inputoutput.html



# TODO time the loop (can overwrite start_time if we want)
# TODO count # of samples/triggers and print at end



# test if file exists & quit if so
if os.path.isfile(fullpath):
    print('ERROR: File already exists.')
    print('Exiting.')
    sys.exit(1)

with open(fullpath, 'w') as f:

    print('\nPress Ctrl+C to stop.\n')

    while True:
    
        # TODO get trigger
        # TODO write timestamp
        pass