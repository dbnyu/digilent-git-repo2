"""Wait for trigger pulses on Scope input and record timestamps of [this] host PC to file.

    WARNING: If using a laptop, it should be plugged in to power source, to avoid
            low-power USB mode/delays (noted on Dell Windows 10 Laptop)
            - Previously noted high drop/corrupt data rate with laptop running on battery-only
                - likely due to a Windows power-save mode
            - THIS MAY INTRODUCE GROUND LOOP ISSUES...





    Doug Brantner
    2/25/2022

    References:
    - Analog Discovery 2:
      - High-Precision timestamps may not be possible:
        - https://forum.digilentinc.com/topic/4798-timestamp-of-digital-input-transition/#comment-19494
        - https://forum.digilentinc.com/topic/19943-question-about-time-stamps-in-exported-csv-files/#comment-55258
        - https://forum.digilentinc.com/topic/19919-analog-discovery-2-and-waveforms-timing-questions/
        - https://forum.digilentinc.com/topic/3670-measuring-frequency/
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

# TODO - would Ext Trigger pin be faster than AnalogIn Trigger???
# TODO would an Arduino + Serial -> python script (or C?) be faster?

# DONE - arduino code for testimg (signal/pulse generator)
# DONE - put this in its own folder (arduino stuff needs its own folder anyway)

# TODO avoid Anaconda imports (numpy, pandas etc.) - works in Cygwin without them (so far)
# TODO loop forever
# TODO wait for trigger
#   TODO - look at FDwfAnalogInStatusTime (SDK docs page 23)
#       - this is probably not what we want: FDwfAnalogInSamplingSourceSet (probably clock source for sample rate?
#   TODO - FDwfAnalogInTriggerHoldOffInfo - holdoff time (depends on MRI pulse/trigger shape)
#   TODO - XXX - probably want this FDwfAnalogInTriggerFilterInfo as 'decimate' to check every sample
#           - otherwise need to wait for avg(N) samples to go high...
#
#   TODO if we do need to fill a dummy buffer (ie. single acquisition):
#       - TODO make buffer as small as possible (0 or 1 sample)
#       - TODO play with trigger offset so that the dummy data is all pre-roll (ie. trigger is last sample in the acq. so that there's no need to wait for additional samples before returning...)
#
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

# From SDK Documentation:
#Note: To ensure consistency between device status and measured data, the following AnalogInStatus*functions
#do not communicate with the device. These functions only return information and data from the last
#FDwfAnalogInStatus call.
# - apparently applies to  FDwfAnalogInStatusTime

# TODO look at this: FDwfAnalogInStatusSample


# USER-EDITABLE OPTIONS:
INPUT_SAMPLE_RATE = 10e6      # Hz  # TODO do we need this? probably set as high as possible...

INPUT_SAMPLE_SIZE = 16384   # sample buffer size (# of samples per acquisition) MAX for extended memory config



SCOPE_VOLT_RANGE_CH1 = 5.0      # oscilloscope ch1 input range (volts)
SCOPE_VOLT_OFFSET_CH1 = 0.      # oscilloscope ch1 offset (volts)  # TODO not yet implemented (probably not needed; zero is preferred)


# Trigger Configuration:
# TODO INPUT_TRIGGER_POSITION_INDEX  do we need this?
SCOPE_TRIGGER_VOLTAGE = 1.0     # volts, threshold to start acquisition
TRIGGER_TYPE = trigtypeEdge
TRIGGER_CONDITION = DwfTriggerSlopeRise


# Parse Input Arguments
parser = argparse.ArgumentParser(description='Analog Discovery 2 - Trigger Timestamp Recorder')
parser.add_argument('-f', '--folder', required=True, help='directory to save files')
# TODO make default 'this' folder?
parser.add_argument('-d', '--desc',   default='timestamps', help='short description for filename')
#parser.add_argument('-p', '--pulseinfo', type=bool, default=False, help='append pulse info to filename')

args = parser.parse_args()
out_folder = args.folder
description = args.desc




def close_file():
    # TODO  - this should be called by sigint handler AND global try/catch
    # TODO maybe we don't need this ('with' is supposedly guaranteed to close the file safely?)
    pass


def signal_handler(signal, frame):

    # TODO close file safely
    print('Exiting...')

    sys.exit(0) # TODO get return code from file closer?


# TODO setup AD2
print('Opening Analog Discovery 2 device...')
dwf = ad2b.load_dwf()
hdwf = c_int()
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf)) # default settings

if hdwf.value == hdwfNone.value:
    szError = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szError);
    print("failed to open device\n"+str(szError.value))
    sys.exit(1)


dwf.FDwfDeviceAutoConfigureSet(hdwf, c_int(0))  # disable auto-configure after each setting change
# Requires calling Configure manually to start device.


# TODO skippipng the entire analog in configure part... see if it does anything...
# lines 596-...


# configure Trigger:
dwf.FDwfAnalogInTriggerAutoTimeoutSet(hdwf, c_double(0)) # disable auto trigger on timeout
dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcDetectorAnalogIn) # one of the analog in channels
dwf.FDwfAnalogInTriggerChannelSet(hdwf, c_int(0)) # first channel
dwf.FDwfAnalogInTriggerTypeSet(hdwf, TRIGGER_TYPE)  # TODO there are options here.
dwf.FDwfAnalogInTriggerLevelSet(hdwf, c_double(SCOPE_TRIGGER_VOLTAGE))
dwf.FDwfAnalogInTriggerConditionSet(hdwf, TRIGGER_CONDITION) 
# TODO do we need this:
#dwf.FDwfAnalogInTriggerPositionSet(hdwf, c_double(INPUT_TRIGGER_POSITION_TIME)) 







# Set up file/folder saving:
print('Saving timestamps in folder: %s' % out_folder)
pathlib.Path(out_folder).mkdir(parents=True, exist_ok=True)


startTime = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
filename = '%s_%s.csv' % (startTime, description)
#filename = '20220225-150808_timestamps.csv'    # test for if file already exists (timestamped names should avoid this anyway)


print('Filename: %s' % filename)
fullpath = os.path.join(out_folder, filename)

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

    print('Enabling AnalogIn...')
    print('Wait at least 2 seconds to stabilize/warmup...')
    # TODO add forced delay?

    print('\nPress Ctrl+C to stop.\n')

    dwf.FDwfAnalogInConfigure(hdwf, c_bool(False), c_bool(True))    # This starts the actual acquisition

    while True:
    
        # TODO get trigger
        # TODO write timestamp
        pass

        # Check if scope triggered; do not copy data to PC (2nd arg)
        dwf.FDwfAnalogInStatus(hdwf, c_int(0), byref(scope_status))
        # TODO declare these:
        dwf.FDwfAnalogInStatusTime(hdwf, byref(trig_utc_sec), byref(trig_ticks), byref(ticks_per_sec))

        # TODO format & write to file; do minimal parsing for quicker loop


# TODO close device (configure false) - this should be protected like file closing...
dwf.FDwfAnalogOutConfigure(hdwf, c_int(WAVEGEN_CHANNEL), c_bool(False))
dwf.FDwfDeviceCloseAll()
dwf.FDwfDeviceClose(hdwf) # from AnalogOut_Pulse.py
