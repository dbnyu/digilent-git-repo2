"""Single Pulse repeated & using 2nd scope as trigger for windowed acquisition.

    Theory:
        - AnalogOut_Pulse.py does a single pulse, repeated N times
            - this can probably be replaced by any excitation pulse waveform
        - The excitation pulse triggers the analogin scope to record a SINGLE acquisition
            - small number of samples will hopefully allow higher sample rates > 2 MHz
        - the small record buffer is copied into RAM, and the scope waits for the next trigger
        - recording 16bit ints, also with the hope of more efficiency/tighter loop timing

    NOTES:
        - seems to work with 1 channel scope up to 100Mhz
            - need to use smaller acquisition window (time period) with high sample rates (ie. buffer/USB bandwidth)
        - optional to convert to voltages
        - plots/pseudo-timescale is reconstructed from indexes, and DOES NOT include dead time 
            aka. 'wait time' between the end of 1 acquisition and the beginning of the next
            - e.g. for a 200usec (0.2ms) echo time and 10ms repetition time, 
              there is 9.8ms per of downtime (per repetition) that is "missing" from this recorded data
              (and therefore the pseudo-A-mode plots as well).
        - scope input range must be set to 50V (Fifty = 5E1 = 10x5V, yes that's correct)
            in order to get the 5V signal (because the input range is PEAK TO PEAK, so 
            the 5V range only gives +/-2.5 volt output range.

    AD2 Max Buffer Sizes:
    - default 8k setting = 8192 = (2^13) samples (each channel)
    - extended 16k setting = 16384 = (2^14) samples 
        - based on max buffer size here:
          https://digilent.com/reference/test-and-measurement/analog-discovery-2/start


    Using AnalogOut_Pulse.py
    and
    AnalogIn_Trigger.py

    Doug Brantner 12/2/2021
"""

# TODO - naming scheme:
#   NO underscores in filenames EXCEPT for two, in specified places: TODO check this user input!
#       to isolate the description & suffix:
#       <date> - <time> _ <description> _ <suffix>.csv
#           (spaces shown for clarity)
#   Filename suffixes:
#       - actual scope data: <name>_data.csv
#       - voltage conversion data: <name>_vconv.csv
#       - all other acquisition settings: <name>_settings.csv


# TODO - expand to larger echo time (buffer size) (max out 8k buffer and then 16k buffer)


# TODO - make the trigger appear at the start of the acquisition, not the middle
#       - TODO maybe some pre-record for scope/pulse sync evaluation...
#       - TODO what is this? FDwfAnalogInSamplingDelaySet (probably not usefuL?)
#       - TODO Try this : FDwfAnalogInTriggerPositionInfo
#       - TODO FDwfAnalogInTriggerPositionSet

# TODO - for multi-pulse excitation pulses, may need this to ignore secondary pulses (within the same excitation wave packet):
#       - TODO FDwfAnalogInTriggerHoldOff
#       - FDwfAnalogInTriggerFilterInfo 
#       - for narrow pulses: FDwfAnalogInTriggerLengthConditionInfo

# TODO - could reshape to M-mode here... since we are capturing exact echo time windows here
#       and then arbitrarily displaying as A-mode (which is inaccurate anyway - see NOTES above)
#       so we could just as easily convert/save as M-mode instead...
#       May be more efficient to store as 16-bit files, (what about WAV files???) 
#       but the orientation of the data (linear vs. matrix) should not affect the file size.

# TODO - could auto-set the acq time window for very high frequencies (ie max it out based on AD2 buffer size)
# TODO - have not tried increasing scope memory w/ AD2 config yet...


# TODO - look at Device_Speed.py - this uses AnalogIO Node Status calls:
# dwf.FDwfAnalogIOChannelNodeStatus(hdwf, 14, 1, byref(t)) # sec to dev
#       - AnalogIO seems to be lower resolution (time/voltage/RF bandwidth???) more akin to Arduino Analog inputs.
#       - TODO are these speed status calls valid for Scope USB speed???
#       - TODO can this be used to get live USB transport speed status???


# TODO - from AnalogIn_Record_Trigger_int16.py:
#        plt.plot(numpy.fromiter(rgSamples1, dtype = numpy.int16))
#        fromiter specifying CORRECT originating datatype...

        



from ctypes import *
from dwfconstants import *

import matplotlib.pyplot as plt
import numpy as np
import datetime
import time
import csv
import sys
import os
import argparse

import ad2_tools as ad2       # my library



# look at AnalogInDigitalIn_Acquisition.py for trigger sync between analog/digital inputs...
# Adding temp save data from custom1MHzWave_record_twochannel_16bit.py


# TODO - convert to voltage here, before saving? (maybe not; save first - most important...)
# DONE - functionalize the pulse waveform/setup to make it easy to change
#   TODO - add wavegen shortname w/ metadata to add to output filename
#   TODO - add another CSV config file output, or append to the existing one?

# TODO 1/19/22: START HERE
# TODO [#A] BUG - seems to be inconsistent trigger timing w/ 16k buffer - 
# TODO look at pulse repetition time (both square and sine waves) 
##### TODO !!! changed this to 20ms for now! #####
# TODO look at trigger holdout (ignore time after initial trigger) - may need to update!

# TODO need a way to trigger the acquisition if using discrete inputs/Rx transducers and isolated wavegen as separate Tx!!!!
# TODO same subplot w/ synced zoom for re-opening saved CSV files


def check_description(s):
    """Check file description & return false if it's invalid.

        s = string (ie. file description)

        Looking for:
        - no underscores in description (only allowed in specific places in filename for later parsing when reading files)
        - TBD...?

    Returns true if description is valid; false otherwise.
    """
    if '_' in s:
        print("\nWARNING: File Description cannot contain underscores '_'")
        return False
    return True


parser = argparse.ArgumentParser(description='Analog Discovery 2, 16-bit 2-ch  Ultrasound Acquisition')
parser.add_argument('-f', '--folder', required=True, help='directory to save files')
parser.add_argument('-d', '--desc',   default='untitled', help='short description for filename')
parser.add_argument('-p', '--pulseinfo', type=bool, default=False, help='append pulse info to filename')
# TODO pulse args? ie. to modify pulse? maybe just a select few ie. voltage...

args = parser.parse_args()
folderPath = args.folder
description = args.desc
append_pulse_info = args.pulseinfo  # TODO not yet implemented


# Check User Input:
if not check_description(description):
    print('ERROR - INVALID FILENAME - Quitting.\n')
    sys.exit(1)


currentTime = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

fname_prefix = '%s_%s' % (currentTime, description)
data_filename =   os.path.join(folderPath, (fname_prefix + '_data.csv'))    # actual acquisition data
vconv_filename = os.path.join(folderPath, (fname_prefix + '_vconv.csv'))    # voltage conversion settings
settings_filename =  os.path.join(folderPath, (fname_prefix + '_settings.csv')) # all other settings
# TODO filename for pulse/scope settings


print(data_filename)






def saveData(myWave1, myWave2):
    """ from custom1MHzWave_record_twochannel_16bit.py

        myWave1,2 = waveform data (TODO more specifics...)


    """
    # TODO add column headers (this will require re-writing parsers too!)
    # TODO remove globals; make them input args

    #currentTime = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    #fname_prefix = '%s_%s' % (currentTime, description)
    #data_filename = os.path.join(folderPath, (fname_prefix + '.csv'))
    

    #data_filename = folderPath +'\\' + description + '_' + currentTime +'.csv' 
    #flag_filename = folderPath +'\\' + description + '_' + currentTime +'_flags.txt' 
    #available_filename = folderPath +'\\' + description + '_' + currentTime +'_available.txt' 

    print('Saving Data to: %s' % data_filename)

    with open(data_filename, 'w', newline='') as wave_file:
        wave_writer = csv.writer(wave_file, delimiter = ',')
        index = 0
        for x in myWave1:

            #wave_writer.writerow([index,(index*inputSamplePeriod),x,myWave2[index]])
            wave_writer.writerow([index,(index*INPUT_SAMPLE_PERIOD ),x,myWave2[index]])
            index = index + 1
            if(index%1000==0):
                print('.',end='')
    print('\nfile written at' + data_filename)

    #with open(flag_filename,'w',newline='') as flag_file:
    #    flag_file.write('flag corrupted:{}, numCorrupted: {}\n'.format(fCorrupted,numCorrupted))
    #    flag_file.write('flag lost: {}, numLost: {}'.format(fLost, numLost))
    #print('\nfile written at' + flag_filename)

    #with open(available_filename,'w',newline='') as available_file:
    #    for i in range(0,len(numAvailable)):
    #        available_file.write('{},{}\n'.format(numAvailable[i],arraynumcorrupted[i]))
    #print('\nfile written at' + available_filename)


# WIP max out buffer to 16k input - max out time window!
# TODO set ch1 range to 5V to really analyze the internal transducer ringing...
# TODO look for a return echo @ 2x time of 180deg sensor...

# Pulser Parameters:
#WAVEGEN_PULSE_TYPE = 'SQUARE_PULSE_1'
WAVEGEN_PULSE_TYPE = 'SINE_N_CYCLES'



# WAVEGEN_N_ACQUISITIONS sets the number of pulses generated, which also determines the number of acquisitions (and run time)
# User Editable:

# SQUARE SINGLE PULSE:
# This is for a single positive-going rectangular pulse, that is repeated every 'wait time'
# (some params are shared with sinewave N cycles)
WAVEGEN_N_ACQUISITIONS = 10        # number of pulse/echo repetitions to acquire
WAVEGEN_WAIT_TIME = 0.02            # seconds between acquisiztions (== TR period, also serves as trigger/acquisition interval)
# TODO NOTE - change wait time to 20ms to account for 16k buffer - make this adjust automatically/make warning work!
WAVEGEN_PULSE_WIDTH = 0.5e-6          # pulse width in seconds (???) TODO CHECK THIS (confirm w/ scope)
#WAVEGEN_PULSE_WIDTH = 1e-6          # pulse width in seconds
# TODO should pulse width be 1/2 usec?
WAVEGEN_PULSE_AMPLITUDE = 5.0       # voltage for pulse
#WAVEGEN_PULSE_AMPLITUDE = 2.5       # voltage for pulse
WAVEGEN_PULSE_V_OFFSET  = 0.        # voltage offset for pulse
WAVEGEN_CHANNEL = 0                 # which output channel to use for pulses (0 or 1)

# SINE WAVE REPEATED N CYCLES:
# This is for N cycles of sine wave:
#WAVEGEN_SINE_N_CYCLES = 10   # number of cycles (sine wave pulse only)
WAVEGEN_SINE_N_CYCLES = 3   # number of cycles (sine wave pulse only)



# Recording Parameters:
# From AnalogIn_Trigger.py
# User Editable:
# NOTE: AD2 will limit sample rates > 100Mhz without any warning.
INPUT_SAMPLE_RATE = 10e6      # Hz 
# NEW: acq time is now secondary/dependent on buffer size (INPUT_SAMPLE_SIZE)
#INPUT_SINGLE_ACQUISITION_TIME = 200e-6        # time to record a single echo (seconds)

#INPUT_SAMPLE_SIZE = 8192    # sample buffer size (# samples per acquisition) MAX for default memory config
INPUT_SAMPLE_SIZE = 16384   # sample buffer size (# of samples per acquisition) MAX for extended memory config

#NEW: setting this based on # of samples desired to have before trigger
INPUT_TRIGGER_POSITION_INDEX = 10   # offset in sample indexes where trigger should start
# ie. 10 samples of pre-roll before trigger, so trigger rising edge is not cut off & clear for analysis (note this gets converted to a time value so it may not be the exact index in the data)
#INPUT_TRIGGER_POSITION_TIME = 0.99 * 0.5 * INPUT_SINGLE_ACQUISITION_TIME  # seconds, trigger position within the acquisition window; default is center (t=0) which wastes 1/2 the buffer
#       0.5 * acq_time = move trigger to beginning of acquisition window 
#               - so that trigger instant is the first sample
#       0.99 * above = allow 1usec of dead time "pre-roll" before trigger
#               - so that we can see 1 pulse period of "intentional nothing" before trigger/pulse
#                   so we can be sure the triggers are perfectly in sync (ie. ensure we capture the correct rising edge)
#               - 0.99 assumes 200usec window so that 1/2 is 100usec and 99% of 100 == 99usec, so there is 1usec of dead pre-roll time in the beginning.

SCOPE_TRIGGER_VOLTAGE = 1.0     # volts, threshold to start acquisition

SCOPE_VOLT_RANGE_CH1 = 5.0      # oscilloscope ch1 input range (volts)
SCOPE_VOLT_OFFSET_CH1 = 0.      # oscilloscope ch1 offset (volts)  # TODO not yet implemented (probably not needed; zero is preferred)

SCOPE_VOLT_RANGE_CH2 = 5.0      # ch2 - volts
SCOPE_VOLT_OFFSET_CH2 = 0.      # ch2 - volts   # TODO not yet implemented

# TODO adjust voltage range for smaller echos? (ie. trigger-only channel can be 5V, but is scope more sensitive for echos if we use lower range? Or is this only for post-processing reconstruction of the voltage values?) 
# ie. does this have any bearing on the int16 values or not???

# TODO smarter input sanitizing/int casting here:

# internal recording parameters:
# for a single acquisition:
# making INPUT_SAMPLE_SIZE the primary input now instead of  INPUT_SINGLE_ACQUISITION_TIME:
#INPUT_SAMPLE_SIZE = int(INPUT_SAMPLE_RATE * INPUT_SINGLE_ACQUISITION_TIME)     # buffer size for 1 acquisition
INPUT_SAMPLE_PERIOD = 1. / INPUT_SAMPLE_RATE    # seconds per acquired sample (aka. sample dt)
INPUT_SINGLE_ACQUISITION_TIME = INPUT_SAMPLE_SIZE / INPUT_SAMPLE_RATE # time duration of 1 full acquisition (sec)

INPUT_TRIGGER_POSITION_TIME = ad2.calc_trigger_pos_from_index(INPUT_TRIGGER_POSITION_INDEX,
                                                              INPUT_SAMPLE_PERIOD,
                                                              INPUT_SINGLE_ACQUISITION_TIME 
                                                              )

# NOTE - for now, ch 1 is the 'main recording channel' so only keeping track of ch1 status... assuming ch2. is 'in sync' with it, but we only care about the beginning of the ch2 signal anyway to see if the triggers/excitation pulses are in sync...
# TODO (above is not fully correct - seems like this is global status for both channels - double check docs!)
scope_status = c_byte()  # scope channel 1 status




# number of samples for all repetitions (for 1 channel):
big_output_len = int(int(INPUT_SAMPLE_SIZE) * int(WAVEGEN_N_ACQUISITIONS))

# NOTE - we are recording int16 type samples; needs to be converted to voltage/double type in post-processing.
acquisition_data_ch1 = (c_int16 * big_output_len)()    # channel 1 main acquisition buffer (over full recording time)
acquisition_data_ch2 = (c_int16 * big_output_len)()    # channel 2 main acquisition buffer (over full recording time)

# troubleshooting: record double-formatted data too to check voltage computation:
#double_data_ch1 = (c_double * big_output_len)()    # channel 1
#double_data_ch2 = (c_double * big_output_len)()    # channel 2



# TODO double check these:
BIG_BUFFER_FULL_TIME = big_output_len * INPUT_SINGLE_ACQUISITION_TIME     # this does NOT include dead time between repetitions! 
print('full record time: %f sec' % BIG_BUFFER_FULL_TIME)

total_record_time = WAVEGEN_N_ACQUISITIONS * WAVEGEN_WAIT_TIME  # just for reference


if INPUT_SAMPLE_RATE > 100e6:
    print('WARNING: sample rates > 1Mhz not supported by Digilent AD2 device!')
    # TODO limit here so plots don't show erroneous high acquisition frequencies?



print('Acquiring %d periods over %.2f seconds...' %  (WAVEGEN_N_ACQUISITIONS, total_record_time))


# setup hardware device:
dwf = ad2.load_dwf()
hdwf = c_int()


version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

dwf.FDwfParamSet(DwfParamOnClose, c_int(0)) # 0 = run, 1 = stop, 2 = shutdown

#open device
print("Opening first device...")
#dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf)) # default settings
dwf.FDwfDeviceConfigOpen(c_int(-1),c_int(1),byref(hdwf))    # memory config #2 - 16k samples

# TODO set config for memory (see AnalogIn_Trigger.py)
# TODO try FDwfDeviceConfigOpen


# TODO print buffer sizes!

if hdwf.value == hdwfNone.value:
    szError = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szError);
    print("failed to open device\n"+str(szError.value))
    quit()

scope_params = ad2.ScopeParams(dwf, hdwf)

print('Testing error function: ' + ad2.get_error(dwf) + '\n')

# the device will be configured only when calling FDwfAnalogOutConfigure
dwf.FDwfDeviceAutoConfigureSet(hdwf, c_int(0))


print('\n\n')

#ad2.print_scope_capabilities(dwf, hdwf)
#print()



def compile_pulse_params():
    """Return lists of all scope parameters.
            names = variable names as strings
            vals = values 
    """
    # TODO not yet implemented - try uzing 'zip'? 
    # idea is to make this able to save to CSV (horizontally)
    # or print (vertically)
    pass


def save_ad2_settings(filepath):
    """Save a CSV file of pulse & scope parameters.

        NOTE that these are scope params as assigned by user.
        This is NOT the actual scope voltage range/offset used
            to compute the voltages from int16 values.
            Those are in a separate file.
    """

    csv_headers = ','.join([
        'WAVEGEN_PULSE_TYPE',   # output params
        'WAVEGEN_N_ACQUISITIONS',
        'WAVEGEN_WAIT_TIME',
        'WAVEGEN_PULSE_WIDTH',
        'WAVEGEN_PULSE_AMPLITUDE',
        'WAVEGEN_PULSE_V_OFFSET',
        'WAVEGEN_CHANNEL',
        'WAVEGEN_SINE_N_CYCLES',
        # input params below:
        'INPUT_SAMPLE_RATE',
        'INPUT_SINGLE_ACQUISITION_TIME',
        'INPUT_TRIGGER_POSITION_TIME',
        'SCOPE_TRIGGER_VOLTAGE',
        'SCOPE_VOLT_RANGE_CH1',
        'SCOPE_VOLT_OFFSET_CH1',
        'SCOPE_VOLT_RANGE_CH2',
        'SCOPE_VOLT_OFFSET_CH2',
        # computed params:
        'INPUT_SAMPLE_SIZE',
        'INPUT_SAMPLE_PERIOD',
        ])

    csv_data = ','.join([ str(val) for val in [
        WAVEGEN_PULSE_TYPE, # output params
        WAVEGEN_N_ACQUISITIONS,
        WAVEGEN_WAIT_TIME,
        WAVEGEN_PULSE_WIDTH,
        WAVEGEN_PULSE_AMPLITUDE,
        WAVEGEN_PULSE_V_OFFSET,
        WAVEGEN_CHANNEL,
        WAVEGEN_SINE_N_CYCLES,
        # input params below:
        INPUT_SAMPLE_RATE,
        INPUT_SINGLE_ACQUISITION_TIME,
        INPUT_TRIGGER_POSITION_TIME,
        SCOPE_TRIGGER_VOLTAGE,
        SCOPE_VOLT_RANGE_CH1,
        SCOPE_VOLT_OFFSET_CH1,
        SCOPE_VOLT_RANGE_CH2,
        SCOPE_VOLT_OFFSET_CH2,
        # computed params:
        INPUT_SAMPLE_SIZE,
        INPUT_SAMPLE_PERIOD,
        ]])

    with open(filepath, 'w') as f:
        f.write(csv_headers)
        f.write('\n')
        f.write(csv_data)






# Wavegen Output
# from AnalogOut_Pulse.py:

def setpulse_single_square_pulse(dwf, hdwf, channel, width, wait, n_acq, amplitude, v_offset=0):
    """Set Waveform Output to a single square pulse (repeating every TR).

        This does a specified number of pulses (n_acq) then stops.

        dwf
        hdwf
        channel = which waveform generator channel to set (0 or 1, python-int)
        width = pulse width (seconds)
        wait  = wait/delay time (aka. TR; seconds)
        n_acq = number of acquisition cycles (int)
        amplitude = pulse amplitude (volts, 0-5)
        v_offset = voltage offset (volts, optional)

    """
    channel = c_int(channel)

    # Single Square Wave Pulse:
    dwf.FDwfAnalogOutNodeEnableSet(hdwf, channel, AnalogOutNodeCarrier, c_bool(True))
    dwf.FDwfAnalogOutIdleSet(hdwf, channel, DwfAnalogOutIdleOffset)
    dwf.FDwfAnalogOutNodeFunctionSet(hdwf, channel, AnalogOutNodeCarrier, funcSquare)
    dwf.FDwfAnalogOutNodeFrequencySet(hdwf, channel, AnalogOutNodeCarrier, c_double(0)) # low frequency # TODO what is this?
    dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, AnalogOutNodeCarrier, c_double(amplitude))
    dwf.FDwfAnalogOutNodeOffsetSet(hdwf, channel, AnalogOutNodeCarrier, c_double(v_offset))
    dwf.FDwfAnalogOutRunSet(hdwf, channel, c_double(width)) # pulse length in time
    dwf.FDwfAnalogOutWaitSet(hdwf, channel, c_double(wait)) # wait length  10 ms = 100 Hz repetition frequency (TR)
    dwf.FDwfAnalogOutRepeatSet(hdwf, channel, c_int(n_acq)) # repeat N times


#def setpulse_single_square_pulse(dwf, hdwf, channel, width, wait, n_acq, amplitude, v_offset=0):
def setpulse_sine_n_cycles(dwf, hdwf, channel, n_cycles, amplitude, v_offset=0, plot=False):
    """Set Waveform Output to N cycles of sine wave.

        NOTE - keeping most defaults (including frequency) for now...

    """
    # TODO revisit this; make it mre modular / expose more input args
    channel = c_int(channel)

    waveBufferLen = 1024 
    waveFreq = 1e6
    wavePeriod = 1.0/waveFreq
    waveformSamples = (c_double*waveBufferLen)()

    pulseWidth = c_double(n_cycles * wavePeriod) # convert n_cycles to time window (seconds)

    # create buffer samples for one period of sine wave
    timespots = np.linspace(0,wavePeriod,num=waveBufferLen)
    index = 0
    for t in timespots:
        waveformSamples[index] = np.sin(t*2*np.pi*waveFreq)
        index = index+1
        # TODO this can be a numpy oneliner but may be tricky casting back to ctypes array...

    # **** PLOT TO DOUBLE CHECK IF THE TIME FORM IS CORRECT ****
    if plot:
        plt.plot(timespots,waveformSamples,marker='.')
        plt.title('wavesamples at ' + str(waveFreq))
        plt.show()
    print("Generating custom waveform...")
    
    # settings for output
    # TODO change to 'channel' var:
    dwf.FDwfAnalogOutNodeEnableSet(hdwf, c_int(0), AnalogOutNodeCarrier, c_bool(True))
    dwf.FDwfAnalogOutNodeFunctionSet(hdwf, c_int(0), AnalogOutNodeCarrier, funcCustom)
    dwf.FDwfAnalogOutNodeDataSet(hdwf, c_int(0), AnalogOutNodeCarrier, waveformSamples, c_int(waveBufferLen))
    # set 
    dwf.FDwfAnalogOutNodeFrequencySet(hdwf, c_int(0), AnalogOutNodeCarrier, c_double(waveFreq))
    dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, c_int(0), AnalogOutNodeCarrier, c_double(amplitude))
    
    # 40000 times to repeat is to be able to have it run for at least a few seconds
    timesToRepeat = c_int(40000)  # no unit
    #pulseWidth = c_double(10e-6)  # in seconds  # TODO does this control # of cycles???

    #pulseWait = c_double(900e-6)  # in seconds [ORIGINAL]
    pulseWait = c_double(WAVEGEN_WAIT_TIME)   # update so that the big global is valid

    dwf.FDwfAnalogOutRunSet(hdwf, channel, pulseWidth) 
    dwf.FDwfAnalogOutWaitSet(hdwf, channel, pulseWait) 
    dwf.FDwfAnalogOutRepeatSet(hdwf, channel, timesToRepeat) 


# Oscilloscope Setup:

# set buffer size from desired time -OR- set buffer size explicitly:
def set_buffer_size_from_time(t):
    """Set acquisition buffer size based on desired time window.
    """
    raise NotImplementedError()
    pass

# TODO this and set_buffer_size(n):
#   """Set buffer size to n samples."""
#       TODO expand memory if necessary.






# END OF FUNCTION DEFINITIONS
# MAIN CODE:


if WAVEGEN_PULSE_TYPE == 'SQUARE_PULSE_1':
    print('Wavegen: Single Square Pulse')
    setpulse_single_square_pulse(dwf, 
                                 hdwf, 
                                 WAVEGEN_CHANNEL,
                                 WAVEGEN_PULSE_WIDTH, 
                                 WAVEGEN_WAIT_TIME,
                                 WAVEGEN_N_ACQUISITIONS,
                                 WAVEGEN_PULSE_AMPLITUDE,
                                 )

elif WAVEGEN_PULSE_TYPE == 'SINE_N_CYCLES':
    print('Wavegen: Sine Wave N Cycles')
    setpulse_sine_n_cycles(dwf,
                           hdwf,
                           WAVEGEN_CHANNEL,
                           WAVEGEN_SINE_N_CYCLES,
                           WAVEGEN_PULSE_AMPLITUDE,
                           v_offset=0,
                           plot=False,
                           )
else:
    print('Invalid WAVEGEN_PULSE_TYPE - Quitting!')
    quit()

# TODO may need a TR counter or a timeout (ie. if we lose some pings, when do we stop?)
# TODO is there a wavegen off trigger? ie. when the automatic pulse train stops????

# TODO could just use a continuous square wave/sine packet and count TR's... maybe ...Pulse is not the right thing to use?
# TODO waht about a digital pin as the timer/trigger (which can then be replaced w/ an MRI trigger when the time comes...?)




# set up acquisition (scopes)
# From AnalogIn_Trigger.py
# TODO do these apply to both channels automatically???
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(INPUT_SAMPLE_RATE))
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(INPUT_SAMPLE_SIZE))

dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))  # ch1 
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(1), c_bool(True))  # ch2
# TODO do we need to disable these at the end? Or does closing the device take care of that?


dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(SCOPE_VOLT_RANGE_CH1))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(1), c_double(SCOPE_VOLT_RANGE_CH2))
# TODO does this matter if using raw 16bit inputs?




# TODO do we need to call dwf.FDwfAnalogInAcquisitionModeSet(hdwf, acqmodeRecord) ???
# p. 26 - acqmodeSingle is the default



#set up trigger
# DONE are both scope channels started by the same single trigger??? YES
# TODO can the 'global trigger bus' also use an external trigger (ie. MRI sync) to trigger BOTH the pulse and recording at the same time???
dwf.FDwfAnalogInTriggerAutoTimeoutSet(hdwf, c_double(0)) #disable auto trigger
dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcDetectorAnalogIn) #one of the analog in channels
dwf.FDwfAnalogInTriggerTypeSet(hdwf, trigtypeEdge)
dwf.FDwfAnalogInTriggerChannelSet(hdwf, c_int(0)) # first channel   # TODO set trigger/real acquisition channels to match Leanna's code
dwf.FDwfAnalogInTriggerLevelSet(hdwf, c_double(SCOPE_TRIGGER_VOLTAGE))
dwf.FDwfAnalogInTriggerConditionSet(hdwf, DwfTriggerSlopeRise) 
dwf.FDwfAnalogInTriggerPositionSet(hdwf, c_double(INPUT_TRIGGER_POSITION_TIME)) 

# TODO use ch2 trigger for ch1 AND ch2 acquisition
# TODO eventuallly if it's consistent/trustworth, maybe can ignore ch2 acquisition...
# TODO OR try to use a single transducer in duplex mode!!!

#or use trigger from other instruments or external trigger
#dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcExternal1) 
#dwf.FDwfAnalogInTriggerConditionSet(hdwf, DwfTriggerSlopeEither) 


#print('\nScope Settings (AFTER setup):') # this also doesn't work if scope is not enabled
#ad2.print_scope_settings(dwf, hdwf)


print('\n')

# TODO does this start the actualy thing 
print("Starting repeated acquisitions")
dwf.FDwfAnalogInConfigure(hdwf, c_bool(False), c_bool(True))    # This starts the actual acquisition


print('\nScope Settings (AFTER configure):')
ad2.print_scope_settings(dwf, hdwf)

scope_params.get_scope_params()

print("Generating pulses")
dwf.FDwfAnalogOutConfigure(hdwf, c_int(WAVEGEN_CHANNEL), c_bool(True))     # this starts actual pulse output

# wait at least 2 seconds with Analog Discovery for the offset to stabilize, before the first reading after device open or offset/range change
#time.sleep(2)  # TODO ignoring this for now... lets see what happens...



# using same index for both ch1/ch2 to keep in sync.
acquisition_data_index = 0  # pointer into acquisition_data_ch1 to write full (single) acquisition blocks
acquisition_data_stride = INPUT_SAMPLE_SIZE * sizeof(c_int16)

# for troubleshooting:
double_ptr = 0 # 
double_stride = INPUT_SAMPLE_SIZE * sizeof(c_double)


# TODO loop optimization (test with profiling!)
# TODO - look into Python JIT compiling - maybe some of these aren't necessary if the compiler will do them automatically:
# - TODO remove all unnecessary function calls (eg. c_int() on constants)
# - TODO pre-compute any constant math values 



# TODO figure out analogin trigger timeout (see p.34 of docs)
# TODO - how do we know if there was a timeout vs. a proper acquisitin? is there a flag in the status?
# TODO - will the buffer be zero'd on a timeout, or is it possible to have a false second reading of the previous buffer?


amplitude = 5.0
# From AnalogIn_Trigger.py:
for iTrigger in range(WAVEGEN_N_ACQUISITIONS):  # TODO this should be until big_buffer is filled (or N_acquistions)

    # keep this for debugging (sometimes the trigger fails & the program hangs)
    #print('start loop %d' % iTrigger)
    #print('.', end='') # print a dot for every acquisition loop (comment out for faster loop)


    # busy wait loop for buffer to finish filling for 1 acquisition
    # new acquisition is started automatically after done state 
    while True:
        dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(scope_status)) # c_int_(1) is a flag to actually transfer data; NOT a channel #.
        if scope_status.value == DwfStateDone.value:
            break
        #time.sleep(0.001) # TODO THIS SHOULD BE MUCH SMALLER O(1-10 microseconds)
        # TODO add this back in? or leave it? would be intersting to time this loop or count it especially at very high sample rates

    
    # TODO try capturing double-formatted data; see if the voltage values are correct there...
    # TODO try profiling double voltages; or ask on forum... is int16 capture actually saving any time?

    # save channel 1 data
    dwf.FDwfAnalogInStatusData16(hdwf, 
                                 c_int(0),
                                 byref(acquisition_data_ch1, acquisition_data_index),
                                 0,
                                 INPUT_SAMPLE_SIZE
                                 )
    # save channel 2 data
    dwf.FDwfAnalogInStatusData16(hdwf, 
                                 c_int(1),
                                 byref(acquisition_data_ch2, acquisition_data_index),
                                 0,
                                 INPUT_SAMPLE_SIZE
                                 )
    # TODO could print ch2. status just to see if it's also complete or not... (since we're not actively checking it yet)

    # troubleshooting (compare SDK voltage values to my computed voltages)
    #dwf.FDwfAnalogInStatusData(hdwf, c_int(0), byref(double_data_ch1, double_ptr), INPUT_SAMPLE_SIZE)
    #dwf.FDwfAnalogInStatusData(hdwf, c_int(1), byref(double_data_ch2, double_ptr), INPUT_SAMPLE_SIZE)
    #double_ptr += double_stride

    acquisition_data_index += acquisition_data_stride 


    # try decreasing the voltage each iteration: (does not work!)
    #amplitude /= 2.0
    #dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, c_int(0), AnalogOutNodeCarrier, c_double(amplitude))



print('Number of loops: %d' % iTrigger)
print('Done...')
dwf.FDwfAnalogOutConfigure(hdwf, c_int(WAVEGEN_CHANNEL), c_bool(False))
# TODO close the scope too?


print('int16 ch1 min: %d' % min(acquisition_data_ch1))
print('int16 ch1 max: %d' % max(acquisition_data_ch1))


# TODO are these 2 lines redundant?:
dwf.FDwfDeviceCloseAll()
dwf.FDwfDeviceClose(hdwf) # from AnalogOut_Pulse.py



# POST PROCESSING:


#print_array(acquisition_data_ch1)

voltage_ch1 = ad2.int16signal2voltage(acquisition_data_ch1, 
                                      scope_params.ch1_v_range,
                                      scope_params.ch1_v_offset,
                                      verbose=False)

voltage_ch2 = ad2.int16signal2voltage(acquisition_data_ch2, 
                                      scope_params.ch2_v_range,
                                      scope_params.ch2_v_offset,
                                      verbose=False)



# saving 16bit data: 
print('Saving raw int16 data...')
saveData(acquisition_data_ch1, acquisition_data_ch2)

print('Saving scope params metadata...')
scope_params.write_vconv_file(vconv_filename)

print('Saving scope settings...')
save_ad2_settings(settings_filename)

print('\n')


print('INPUT_SAMPLE_RATE: %f MHz' % (INPUT_SAMPLE_RATE*1e-6))
print('1 acqusition time: %e sec (%f usec)' % (INPUT_SINGLE_ACQUISITION_TIME, INPUT_SINGLE_ACQUISITION_TIME*1e6))
if INPUT_SINGLE_ACQUISITION_TIME >= WAVEGEN_WAIT_TIME: 
    print('\tWARNING: buffer time > pulse wave time (may get multiple excitations per Receive period)!')


print('full record time : %f sec' % BIG_BUFFER_FULL_TIME) 
print()
print('INPUT_SAMPLE_SIZE: %d (for 1 acquisition)' % INPUT_SAMPLE_SIZE)
print('full record N samples: %d' % big_output_len) 

approx_usb_bitrate = (16 * big_output_len) / BIG_BUFFER_FULL_TIME   # assuming data is transported as 2-byte values
print('approx USB bitrate: %f bits/sec' % approx_usb_bitrate)



pseudotimescale = INPUT_SAMPLE_PERIOD * np.arange(big_output_len)
# NOTE - this is ONLY considering the "small t" echo timescale; it DOES NOT account
# for the down time/delay between the end of an echo window and the next pulse
# e.g. for a 200usec (0.2ms) echo time and 10ms repetition time, 
# there is 9.8ms per of time (per repetition) that is "missing" from this scale and plot:

# TEMP DELETE THIS TODO
# plot int16 values against pseudo-time
#plt.plot(pseudotimescale, acquisition_data_ch1[:], '.-', label='Ch1 (int16)')
#plt.plot(pseudotimescale, acquisition_data_ch2[:], '.-', label='Ch2 (int16)')
#plt.xlabel('Index')
#plt.ylabel('int16 "voltage"')
#plt.legend()
#plt.show()
#sys.exit()






print('\n\n')
print('Scope Ch1 Recorded Stats:')
print('min voltage: %f (V)' % np.min(voltage_ch1))
print('max voltage: %f (V)' % np.max(voltage_ch1))

print('Scope Ch2 Recorded Stats:')
print('min voltage: %f (V)' % np.min(voltage_ch2))
print('max voltage: %f (V)' % np.max(voltage_ch2))


print()
print('Ch1/Ch2 Comparison:')
difference = voltage_ch2 - voltage_ch1
difference_norm = np.linalg.norm(difference)
difference_sum = np.sum(difference_norm)
difference_mean = np.mean(difference_norm)

print('Mean of difference: %f' % difference_norm)
print('Sum of difference: %f (over all samples)' % difference_sum)
print('2-Norm of ch2-ch1: %f' % difference_norm)

print('min abs. difference: %f (V)' % np.min(np.abs(difference)))
print('max abs. difference: %f (V)' % np.max(np.abs(difference)))

if np.max(difference) == 0:
    print('\t(max abs. difference is exactly zero.)')

# TODO - NOTE - exact difference == 0 for so many samples is unlikely...
#   however, we started with 16bit int discretized values, so that makes it slightly less strange... 

print('\n\n')






### Plotting ###
# speed of sound values from https://itis.swiss/virtual-population/tissue-properties/database/acoustic-properties/speed-of-sound/
C_WATER = 1482.3    # m/s
C_AIR = 343.0       # m/s

C = C_WATER

def time2mm(t):
    """Convert time to millimeters using global C speed of sound.
        t = time [sec]
    """
    return 1000. * C * t

def mm2time(d):
    """Convert millimeters to time [sec], using global C.
        d = distance array [mm]
    """
    return (1. / (1000. * C)) * d


# plot int16 values against indexes
#plt.plot(acquisition_data_ch1[:], '.-', label='Ch1 (int16)')    

# plot int16 values against pseudo-time
#plt.plot(pseudotimescale, acquisition_data_ch1[:], '.-', label='Ch1 (int16)')
#plt.plot(pseudotimescale, acquisition_data_ch2[:], '.-', label='Ch2 (int16)')



# plot proper voltages against indexes
#plt.plot(voltage_ch1, '.-', label='Ch. 1 (V)')
#plt.plot(voltage_ch2, '.-', label='Ch. 2 (V)')
#plt.title('Voltage vs. Index')
#plt.xlabel('Index')
#plt.ylabel('Volts')
#plt.legend()
#plt.show()




# plot proper voltages against pseudo-time
plt.plot(pseudotimescale, voltage_ch1, '.-', label='Ch. 1 (V)')
plt.plot(pseudotimescale, voltage_ch2, '.-', label='Ch. 2 (V)')
plt.title('%d Acq. @ %.2e Hz Sample Rate (%.2e s window)' % (WAVEGEN_N_ACQUISITIONS, INPUT_SAMPLE_RATE, INPUT_SINGLE_ACQUISITION_TIME))
plt.xlabel('Seconds (TR delays not shown!)')
plt.ylabel('Volts')
plt.legend()
#plt.xlim([0, 1000e-6])
plt.show()




# plot distance and time together (voltage)
fig, ax = plt.subplots()
distscale = time2mm(pseudotimescale)
#ax.plot(pseudotimescale, voltage_ch1, '.-', label='Ch. 1 (V)')
#ax.plot(pseudotimescale, voltage_ch2, '.-', label='Ch. 2 (V)')
ax.plot(distscale, voltage_ch1, '.-', label='Ch. 1 (V)')
ax.plot(distscale, voltage_ch2, '.-', label='Ch. 2 (V)')
ax.legend()
#plt.title('%d Acq. @ %.2e Hz Sample Rate (%.2e s window)' % (WAVEGEN_N_ACQUISITIONS, INPUT_SAMPLE_RATE, INPUT_SINGLE_ACQUISITION_TIME))
#plt.title('%s @ SR=%.2e Hz (TR=%.2e s)' % (description, INPUT_SAMPLE_RATE, INPUT_SINGLE_ACQUISITION_TIME))
plt.title('%s @ SR=%.2e Hz (TR=%.2e s)' % (description, INPUT_SAMPLE_RATE, INPUT_SINGLE_ACQUISITION_TIME))

#ax.set_xlabel('Time [sec] (TR waits omitted)')
ax.set_xlabel('Distance [mm] (take diffs!)')
ax.set_ylabel('Volts')    

#ax2 = ax.secondary_xaxis('top', functions=(time2mm, mm2time))
ax2 = ax.secondary_xaxis('top', functions=(mm2time, time2mm))
ax2.set_xlabel('Time [sec] (TR waits omitted)')
#ax2.set_xlabel('Distance [mm] (diffs only!)')
plt.show()




# plot 2 channels as separate subplots
# distance as X axis; linked zoom on x axis:
# https://stackoverflow.com/questions/4200586/matplotlib-pyplot-how-to-zoom-subplots-together
ax_ch1 = plt.subplot(2, 1, 1)
ax_ch1.plot(distscale, voltage_ch1, '.-', label='Ch. 1 (V)')

plt.title('%s @ SR=%.2e Hz (TR=%.2e s)' % (description, INPUT_SAMPLE_RATE, INPUT_SINGLE_ACQUISITION_TIME))

ax_ch2 = plt.subplot(2, 1, 2, sharex=ax_ch1)
ax_ch2.plot(distscale, voltage_ch2, '.-', color='tab:orange', label='Ch. 2 (V)')

ax_ch1.set_xlabel('Distance [mm] (take diffs!)')
ax_ch2.set_xlabel('Distance [mm] (take diffs!)')
ax_ch1.set_ylabel('Ch. 1 Volts')    
ax_ch2.set_ylabel('Ch. 2 Volts')    
#plt.title('Signals Shown Separately')
plt.show()





#################
# Plot error:
#plt.plot(difference, '.-', label='Ch2 - Ch1')
#plt.title('Error @ %.2e Hz Sample Rate (%.2e s window)' % (INPUT_SAMPLE_RATE, INPUT_SINGLE_ACQUISITION_TIME))
#plt.xlabel('Seconds (TR delays not shown!)')
#plt.ylabel('Voltage')
#plt.legend()
#plt.show()


#################
# Bland-Altman of ch1 vs. ch2
#ad2.bland_altman(voltage_ch1, voltage_ch2)






#################
## Troubleshooting voltage values:
#
#err_ratio = np.divide(double_data_ch1, voltage_ch1)
#
#plt.plot(pseudotimescale, voltage_ch1, '.-', label='int16 ch1')
#plt.plot(pseudotimescale, double_data_ch1, '.-', label='double ch1')
#plt.plot(pseudotimescale, err_ratio, '.-', label='err ratio')
#plt.title('int16 voltage conversion vs. builtin double values')
#plt.legend()
#plt.xlabel('pseudotime')
#plt.ylabel('Volts')
#plt.show()
