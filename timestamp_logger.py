"""Wait for trigger pulses on Scope input and record timestamps of [this] host PC to file.

    WARNING: If using a laptop, it should be plugged in to power source, to avoid
            low-power USB mode/delays (noted on Dell Windows 10 Laptop)
            - Previously noted high drop/corrupt data rate with laptop running on battery-only
                - likely due to a Windows power-save mode
            - THIS MAY INTRODUCE GROUND LOOP ISSUES...


    Notes:
        - We may be approaching the trigger/re-arm limits of the AD2 device (testing ~2ms TR)
        - Max "tick" resolution may not be very high
            - number of ticks/sec as recorded in files is ~1000 so far... so best precision is 1ms???
        - Min buffer size is 16 - so it will always acquire at least 16 samples before being "done"
            - this may affect the max re-arm/re-trigger rate



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



    Doug Brantner
    2/25/2022
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


# TODO  !!! write raw bytes to file instead of ASCII. !!!

# TODO - would Ext Trigger pin be faster than AnalogIn Trigger???
# TODO would an Arduino + Serial -> python script (or C?) be faster?

# DONE - arduino code for testimg (signal/pulse generator)
# DONE - put this in its own folder (arduino stuff needs its own folder anyway)

# TODO avoid Anaconda imports (numpy, pandas etc.) - works in Cygwin without them (so far)
#
# do we  need to fill a dummy buffer (ie. single acquisition)?:
#       - TRYING THIS make buffer as small as possible (0 or 1 sample)
#       - TODO play with trigger offset so that the dummy data is all pre-roll (ie. trigger is last sample in the acq. so that there's no need to wait for additional samples before returning...)
#           - hopefully minimal delay with sample size == 1.
#
#   DONE - record raw (simplest/fastest representation) of timestamp & parse to human later?
# IN PROGRESS write to file
#   TODO ramdisk/tmpfile? for faster writing?
#   TODO could lead to memory issues with other recordings ( TOF camera) or long acquisitions...
#   TODO may need to do some code profiling to make sure diskwrites are fast enough
#   TODO diagnostic function to troubleshoot?
# TODO indicator onscreen?
#   NOTE screen I/O can be slow
#   - may not be possible while keeping loop as fast as possible...
#   TODO on linux, can just tail/follow the output file, or 'tee'
#   TODO make this optional (ideally without 'if' statements) to display or not display full strings
#   TODO also just a 'period' to show that it's working...
#   TODO pulses are order of milliseconds... so every 1000th pulse shouldn't hurt too much
#       TODO look for delays that correlate with this just to be safe...
# TODO - optimization - only get the TIME and not the full DATE/TIME, save some bits???
#   - only need to store the date once ie. in filename...
#   - not sure if this would make a difference...using AD2 builtin time function which returns seconds since Unix Epoch as 3 sets of int
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



# USER-EDITABLE OPTIONS:
INPUT_SAMPLE_RATE = 100e6    # Hz (100MHz max)
INPUT_SAMPLE_SIZE = 16       # sample buffer size  - minimum appears to be 16 (anything less defaults back to 16)
# TODO - if this can't be avoided maybe we need to set the trigger position ...


# Trigger Configuration: TODO ADJUST FOR MRI PULSES:
SCOPE_VOLT_RANGE_CH1 = 5.0      # oscilloscope ch1 input range (volts) OPTIONS 5 or 50 only!
#SCOPE_VOLT_OFFSET_CH1 = 0.     # oscilloscope ch1 offset (volts)  # TODO not yet implemented (probably not needed; zero is preferred)
SCOPE_TRIGGER_VOLTAGE = 1.0     # trigger threshold (volts)
#TRIGGER_HOLDOFF_TIME = 20e-6    # 10usec pulse width x2
TRIGGER_HOLDOFF_TIME = 10e-6    # 10usec pulse width x2

TRIGGER_TYPE = trigtypeEdge
TRIGGER_CONDITION = DwfTriggerSlopeRise
TRIGGER_FILTER = filterDecimate

# TODO INPUT_TRIGGER_POSITION_INDEX  do we need this? !!!XXX!!!! - sample size min is 16
# TODO look at this: FDwfAnalogInStatusSample




# Parse Input Arguments
parser = argparse.ArgumentParser(description='Analog Discovery 2 - Trigger Timestamp Recorder')
parser.add_argument('-f', '--folder', required=True, help='directory to save files')
# TODO make default 'this' folder?
parser.add_argument('-d', '--desc',   default='timestamps', help='short description for filename')
#parser.add_argument('-p', '--pulseinfo', type=bool, default=False, help='append pulse info to filename')

args = parser.parse_args()
out_folder = args.folder
description = args.desc


# globals for loop stats (need to be global for signal_handler at end)
loop_count = 0      # number of loops/triggers received 

def close_file():
    # TODO  - this should be called by sigint handler AND global try/catch
    # TODO maybe we don't need this ('with' is supposedly guaranteed to close the file safely?)
    pass


def close_AD2_device():
    """Handler to close & disable the Analog Discovery 2 device before exit."""

    print('Stopping device...')
    #dwf.FDwfAnalogOutConfigure(hdwf, c_int(WAVEGEN_CHANNEL), c_bool(False)) # not used here.
    dwf.FDwfAnalogInConfigure(hdwf, c_bool(False), c_bool(False)) # stop acquisitions
    dwf.FDwfDeviceCloseAll()
    dwf.FDwfDeviceClose(hdwf)

# TODO make this easier to integrate (how?... want to avoid 'if' statements in loop...)
#def debug_plot():
#    # DEBUG ONLY:
#    import numpy as np
#    import matplotlib.pyplot as plt
#
#    t = (1./INPUT_SAMPLE_RATE) * np.arange(debug_buffer_size)
#
#    print('Debug Plot...')
#    plt.plot(t, acquisition_data_ch1, '.-')
#    plt.xlabel('Time (s)')
#    plt.ylabel('Volts')
#    plt.show()


def signal_handler(signal, frame):
    """Handler for Control+C end of program.

        All cleanup/printing goes here.
    """

    loop_end_time = datetime.datetime.now()

    close_AD2_device()


    loop_time_duration = loop_end_time - loop_start_time
    print('Got %d triggers in %d seconds.' % (loop_count, loop_time_duration.total_seconds()))

    if loop_count > 0:
        tr = float(loop_time_duration.total_seconds()) / loop_count
        tr *= 1000  # convert to milliseconds
        print('(Rough TR = %.3f ms)' % tr)
        # TODO NOTE this can be very innacurate for small time periods/start/stop by hand with inherent delays


    # TODO close file safely    (should be handled automatically by 'with' context manager)
    print('Exiting...')

    #debug_plot()    # DEBUG ONLY

    sys.exit(0) # TODO get return code from file closer?





# setup AD2
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

# Configure Scope Input
# TODO make channel a variable (need to find all c_int(0)'s that refer to the channel...)
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(INPUT_SAMPLE_RATE))
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(INPUT_SAMPLE_SIZE))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(SCOPE_VOLT_RANGE_CH1))
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))  # ch1 
# TODO dwf.FDwfAnalogInAcquisitionModeSet ?? 
# default seemsto be 0 which *should* re-arm the trigger automatically after each acquisition


# configure Trigger:
dwf.FDwfAnalogInTriggerAutoTimeoutSet(hdwf, c_double(0)) # disable auto trigger on timeout
dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcDetectorAnalogIn) # one of the analog in channels
dwf.FDwfAnalogInTriggerChannelSet(hdwf, c_int(0)) # first channel
dwf.FDwfAnalogInTriggerTypeSet(hdwf, TRIGGER_TYPE)  # TODO there are options here.
dwf.FDwfAnalogInTriggerLevelSet(hdwf, c_double(SCOPE_TRIGGER_VOLTAGE))
dwf.FDwfAnalogInTriggerConditionSet(hdwf, TRIGGER_CONDITION) 
dwf.FDwfAnalogInTriggerHoldOffSet(hdwf, c_double(TRIGGER_HOLDOFF_TIME))
dwf.FDwfAnalogInTriggerFilterSet(hdwf, c_int(0), filterDecimate)    # NOTE - default is filterAverage- this could be slowing us down...

# TODO do we need this?:
#dwf.FDwfAnalogInTriggerPositionSet(hdwf, c_double(INPUT_TRIGGER_POSITION_TIME)) 







# Set up file/folder saving:
print('Saving timestamps in folder: %s' % out_folder)
pathlib.Path(out_folder).mkdir(parents=True, exist_ok=True)


startTime = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
filename = '%s_%s.csv' % (startTime, description)


print('Filename: %s' % filename)
fullpath = os.path.join(out_folder, filename)



# register signal handler (before/right after file is actually opened)
# TODO make sure this works cross-platform!
# works in Powershell (Windows 10 host/Anaconda)
# works in Cygwin (Windows 10 host/Anaconda python but no libraries/env)
signal.signal(signal.SIGINT, signal_handler)



# NOTE: 'with' block should close file safely even with an exception:
# "It is good practice to use the with keyword when dealing with file objects. 
# The advantage is that the file is properly closed after its suite finishes, 
# even if an exception is raised at some point. Using with is also much shorter than 
# writing equivalent try-finally blocks"
# - from https://docs.python.org/3/tutorial/inputoutput.html


# Buffers (single vars) to receive time data from scope trigger:
# TODO can we hardcode as c_uint32/64?
trig_utc_sec  = c_uint()
trig_ticks    = c_uint()
ticks_per_sec = c_uint()





# test if file exists & quit if so
if os.path.isfile(fullpath):
    print('ERROR: File already exists.')
    print('Exiting.')
    sys.exit(1)


# DEBUG ONLY:
#debug_buffer_n_count = 10
#debug_buffer_size = debug_buffer_n_count * INPUT_SAMPLE_SIZE
##acquisition_data_ch1 = (c_int16 * debug_buffer_size)()    # channel 1 main acquisition buffer (over full recording time)
##acquisition_data_stride = INPUT_SAMPLE_SIZE * sizeof(c_int16)
#
#acquisition_data_ch1 = (c_double * debug_buffer_size)()
#acquisition_data_stride = INPUT_SAMPLE_SIZE * sizeof(c_double)
#
#acquisition_data_index = 0


# Scope Info/Debugging:
scope_status = c_byte()  # scope channel 1 status
holdoff_conf = c_double()   # confirm trigger holdoff time
filter_conf = c_int()       # confirm trigger filter
acqmode_conf = c_int()      # confirm acquisition mode  (TODO is the type correct? can't find ACQMODE type in python consts file)
buffersize_conf = c_int()   # buffer size
2
buffersize_min = c_int()
buffersize_max = c_int()





with open(fullpath, 'w') as f:

    print('Enabling Analog Input...')
    print('Please Wait at least 2 seconds to stabilize/warmup...')



    # Enable Scope:
    dwf.FDwfAnalogInConfigure(hdwf, c_bool(False), c_bool(True))    # This starts the actual acquisition

    
    # Confirm Scope Settings (must be enabled first):
    dwf.FDwfAnalogInTriggerHoldOffGet(hdwf, byref(holdoff_conf))
    print('Trigger Holdoff Confirm: ', holdoff_conf.value, ' sec')

    dwf.FDwfAnalogInTriggerFilterGet(hdwf, c_int(0), byref(filter_conf))
    print('Trigger Filter Confirm: %d' % filter_conf.value)

    dwf.FDwfAnalogInAcquisitionModeGet(hdwf, byref(acqmode_conf))
    print('Acquisition Mode Confirm: %d' % acqmode_conf.value)

    dwf.FDwfAnalogInBufferSizeInfo(hdwf, byref(buffersize_min), byref(buffersize_max))
    print('Min Buffer Size: %d' % buffersize_min.value)
    print('Max Buffer Size: %d' % buffersize_max.value)

    dwf.FDwfAnalogInBufferSizeGet(hdwf, byref(buffersize_conf))
    print('Buffer Size Confirm: %d' % buffersize_conf.value)

    # check for AD2 errors before starting
    ad2b.check_and_print_error(dwf)


    print('\nPress Ctrl+C to stop.\n')
    loop_start_time = datetime.datetime.now()
    while True: # main loop


        # Check if scope triggered; do not copy data to PC (2nd arg)
        # status check loop - busy wait until trigger/"Acquisition" is ready:
        while True:
            dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(scope_status)) # TODO change back to 0?
            # TODO what does above c_int do? are the triggers still accurate with 0?
            # TODO is it introducing a delay (by transferring acquired data over USB) and adding delay to triggers?
            # TODO
            if scope_status.value == DwfStateDone.value:
                break
                #print('|', end='', flush=True)  # DEBUG ONLY


        # get time from trigger:
        # (we are ignoring the actual data acquired, only need the time.)
        dwf.FDwfAnalogInStatusTime(hdwf, byref(trig_utc_sec), byref(trig_ticks), byref(ticks_per_sec))


        # Write ASCII Data to file (slower, larger file):
        f.write(repr(trig_utc_sec.value)  + ',' + \
                repr(trig_ticks.value)    + ',' + \
                repr(ticks_per_sec.value) + '\n')
        # TODO is \n sufficient or do we need Windows newline?
        # TODO is repr necessary?

        # TODO try to write raw bytes (maybe fixed bytes, no separators,
        #   - ie. 3 values, each value is 4 bytes then AAAABBBBCCCCAAAABBBBCCCC...
        #   - so no newlines, etc. and every 12th byte is the next set of values

        # DEBUG ONLY: capture scope data
        #if loop_count < debug_buffer_n_count:
        #    # int 16 data:
        #    #dwf.FDwfAnalogInStatusData16(hdwf, 
        #    #                             c_int(0),
        #    #                             byref(acquisition_data_ch1, acquisition_data_index),
        #    #                             0,
        #    #                             INPUT_SAMPLE_SIZE
        #    #                             )

        #    # double (actual voltage) data:
        #    dwf.FDwfAnalogInStatusData(hdwf,
        #                               c_int(0),
        #                               byref(acquisition_data_ch1, acquisition_data_index),
        #                               INPUT_SAMPLE_SIZE
        #                               )

        #    acquisition_data_index += acquisition_data_stride 

        loop_count += 1




    print('Error: Hit End of Loop.')    # should never reach here; signit handler should catch Ctrl+C
print('Error: Hit end of context manager')
