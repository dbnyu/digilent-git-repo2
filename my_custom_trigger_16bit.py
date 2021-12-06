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

    Using AnalogOut_Pulse.py
    and
    AnalogIn_Trigger.py

    Doug Brantner 12/2/2021
"""

# TODO - check voltage conversion - only showing 2.5V on plots here, but should be 5V
#        - also shows up as 5V on external (Doug's Rigol) scope (with 1x probe attenuation setting & direct coax input)
#           (the pulse is 0-5V on external scope, which should be correct)

# TODO - make the trigger appear at the start of the acquisition, not the middle
#       - TODO maybe some pre-record for scope/pulse sync evaluation...

# TODO - could reshape to M-mode here... since we are capturing exact echo time windows here
#       and then arbitrarily displaying as A-mode (which is inaccurate anyway - see NOTES above)
#       so we could just as easily convert/save as M-mode instead...
#       May be more efficient to store as 16-bit files, (what about WAV files???) 
#       but the orientation of the data (linear vs. matrix) should not affect the file size.

# TODO - could auto-set the acq time window for very high frequencies (ie max it out based on AD2 buffer size)
# TODO - have not tried increasing scope memory w/ AD2 config yet...


from ctypes import *
from dwfconstants import *
import matplotlib.pyplot as plt
import numpy as np
import sys
import time

# TODO look at AnalogInDigitalIn_Acquisition.py for trigger sync between analog/digital inputs...

def print_array(arr, line_len=10):
    """print a Ctypes array, with optional line breaks
    
        arr = ctypes array
        line_len = print a newline after this many entries; 
                    set to zero or None to print 1 line
    """
    for i in range(len(arr)):
        print(str(arr[i]) + ',', end='')

        if line_len > 0  and (i+1) % line_len == 0: # i+1 because of zero based index?
            print()




# Pulser Parameters (Wavegen Output #1):
# This is for a single positive-going rectangular pulse, that is repeated every 'wait time'
# WAVEGEN_N_ACQUISITIONS sets the number of pulses generated, which also determines the number of acquisitions (and run time)

# User Editable:
WAVEGEN_N_ACQUISITIONS = 100        # number of pulse/echo repetitions to acquire
WAVEGEN_WAIT_TIME = 0.01            # seconds between acquisiztions (== TR period)
WAVEGEN_PULSE_WIDTH = 1e-6          # pulse width in seconds (???) TODO CHECK THIS (confirm w/ scope)
# TODO should pulse width be 1/2 usec?


# Recording Parameters:
# From AnalogIn_Trigger.py
# User Editable:
# NOTE: AD2 will limit sample rates > 100Mhz without any warning.
INPUT_SAMPLE_RATE = 10e6      # Hz 
INPUT_SINGLE_ACQUISITION_TIME = 200e-6        # time to record a single echo (seconds)

SCOPE_TRIGGER_VOLTAGE = 1.0     # volts, threshold to start acquisition

SCOPE_VOLT_RANGE_CH1 = 5.0      # oscilloscope ch1 input range (volts)
SCOPE_VOLT_OFFSET_CH1 = 0.      # oscilloscope ch1 offset (volts)  # TODO not yet implemented (only using for plotting atm.)
# TODO adjust voltage range for smaller echos? (ie. trigger-only channel can be 5V, but is scope more sensitive for echos if we use lower range? Or is this only for post-processing reconstruction of the voltage values?) 
# ie. does this have any bearing on the int16 values or not???

# TODO smarter input sanitizing/int casting here:

# internal recording parameters:
# for a single acquisition:
INPUT_SAMPLE_SIZE = int(INPUT_SAMPLE_RATE * INPUT_SINGLE_ACQUISITION_TIME)     # buffer size for 1 acquisition
INPUT_SAMPLE_PERIOD = 1. / INPUT_SAMPLE_RATE    # seconds per acquired sample
sts = c_byte()



big_output_len = int(int(INPUT_SAMPLE_SIZE) * int(WAVEGEN_N_ACQUISITIONS))
big_output_buffer = (c_int16 * big_output_len)()
#print_array(big_output_buffer, 0)


# TODO double check these:
BIG_BUFFER_FULL_TIME = big_output_len * INPUT_SINGLE_ACQUISITION_TIME     # this does NOT include dead time between repetitions! 
print('full record time: %f sec' % BIG_BUFFER_FULL_TIME)

total_record_time = WAVEGEN_N_ACQUISITIONS * WAVEGEN_WAIT_TIME  # just for reference


if INPUT_SAMPLE_RATE > 100e6:
    print('WARNING: sample rates > 1Mhz not supported by Digilent AD2 device!')
    # TODO limit here so plots don't show erroneous high acquisition frequencies?



print('Acquiring %d periods over %.2f seconds...' %  (WAVEGEN_N_ACQUISITIONS, total_record_time))



if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

hdwf = c_int()
channel = c_int(0)  # wavegen channel #1


version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

dwf.FDwfParamSet(DwfParamOnClose, c_int(0)) # 0 = run, 1 = stop, 2 = shutdown

#open device
print("Opening first device...")
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

# TODO set config for memory (see AnalogIn_Trigger.py)
# TODO print buffer sizes!

if hdwf.value == hdwfNone.value:
    szError = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szError);
    print("failed to open device\n"+str(szError.value))
    quit()

# the device will be configured only when calling FDwfAnalogOutConfigure
dwf.FDwfDeviceAutoConfigureSet(hdwf, c_int(0))





# Wavegen Output
# from AnalogOut_Pulse.py:

# TODO break out important settings to user-edit section up top (amplitude, etc)

# Single Square Wave Pulse:
dwf.FDwfAnalogOutNodeEnableSet(hdwf, channel, AnalogOutNodeCarrier, c_bool(True))
dwf.FDwfAnalogOutIdleSet(hdwf, channel, DwfAnalogOutIdleOffset)
dwf.FDwfAnalogOutNodeFunctionSet(hdwf, channel, AnalogOutNodeCarrier, funcSquare)
dwf.FDwfAnalogOutNodeFrequencySet(hdwf, channel, AnalogOutNodeCarrier, c_double(0)) # low frequency
dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, AnalogOutNodeCarrier, c_double(5))
#dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, AnalogOutNodeCarrier, c_double(-5))    # TODO not clear if negative square amplitude is valid? probalby not..
dwf.FDwfAnalogOutNodeOffsetSet(hdwf, channel, AnalogOutNodeCarrier, c_double(0))
dwf.FDwfAnalogOutRunSet(hdwf, channel, c_double(WAVEGEN_PULSE_WIDTH)) # pulse length in time (?)
dwf.FDwfAnalogOutWaitSet(hdwf, channel, c_double(WAVEGEN_WAIT_TIME)) # wait length  10 ms = 100 Hz repetition frequency (TR)
dwf.FDwfAnalogOutRepeatSet(hdwf, channel, c_int(WAVEGEN_N_ACQUISITIONS)) # repeat N times
# TODO see if square wave can go +/- or only +????




# TODO may need a TR counter or a timeout (ie. if we lose some pings, when do we stop?)
# TODO is there a wavegen off trigger? ie. when the automatic pulse train stops????

# TODO could just use a continuous square wave/sine packet and count TR's... maybe ...Pulse is not the right thing to use?
# TODO waht about a digital pin as the timer/trigger (which can then be replaced w/ an MRI trigger when the time comes...?)




# From AnalogIn_Trigger.py
#set up acquisition
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(INPUT_SAMPLE_RATE))
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(INPUT_SAMPLE_SIZE))
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))
# TODO enable channel 2 also? (YES need to enable separately) - look at dualrecord (Leanna)

dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(SCOPE_VOLT_RANGE_CH1))
# TODO channelrangeset for ch2
# TODO does this matter if using raw 16bit inputs?



#set up trigger
dwf.FDwfAnalogInTriggerAutoTimeoutSet(hdwf, c_double(0)) #disable auto trigger
dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcDetectorAnalogIn) #one of the analog in channels
dwf.FDwfAnalogInTriggerTypeSet(hdwf, trigtypeEdge)
dwf.FDwfAnalogInTriggerChannelSet(hdwf, c_int(0)) # first channel
dwf.FDwfAnalogInTriggerLevelSet(hdwf, c_double(SCOPE_TRIGGER_VOLTAGE))
dwf.FDwfAnalogInTriggerConditionSet(hdwf, DwfTriggerSlopeRise) 


# TODO use ch2 trigger for ch1 AND ch2 acquisition
# TODO eventuallly if it's consistent/trustworth, maybe can ignore ch2 acquisition...
# TODO OR try to use a single transducer in duplex mode!!!

#or use trigger from other instruments or external trigger
#dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcExternal1) 
#dwf.FDwfAnalogInTriggerConditionSet(hdwf, DwfTriggerSlopeEither) 




# TODO does this start the actualy thing 
print("Starting repeated acquisitions")
dwf.FDwfAnalogInConfigure(hdwf, c_bool(False), c_bool(True))    # This starts the actual acquisition


print("Generating pulses")
dwf.FDwfAnalogOutConfigure(hdwf, channel, c_bool(True))     # this starts actual pulse output

# wait at least 2 seconds with Analog Discovery for the offset to stabilize, before the first reading after device open or offset/range change
#time.sleep(2)  # TODO ignoring this for now... lets see what happens...


# From AnalogIn_Trigger.py:

# TODO copy to main output buffer...



big_output_pointer = 0  # pointer into big_output_buffer to write full (single) acquisition blocks
big_output_stride = INPUT_SAMPLE_SIZE * sizeof(c_int16)


# TODO figure out analogin trigger timeout (see p.34 of docs)
# TODO change name; itrigger is a vestige of one of the example files
for iTrigger in range(WAVEGEN_N_ACQUISITIONS):  # TODO this should be until big_buffer is filled (or N_acquistions)
    # new acquisition is started automatically after done state 

    #print('start loop %d' % iTrigger)
    #print('.', end='') # print a dot for every acquisition loop (comment out for faster loop)

    # busy wait loop for buffer to finish filling for 1 acquisition
    while True:
        dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
        if sts.value == DwfStateDone.value :
            break
        #time.sleep(0.001) # TODO THIS SHOULD BE MUCH SMALLER O(1-10 microseconds)
        # TODO add this back in? or leave it? would be intersting to time this loop or count it especially at very high sample rates
    
    #dwf.FDwfAnalogInStatusData(hdwf, 0, rgdSamples, 8192) # get channel 1 data
    #dwf.FDwfAnalogInStatusData(hdwf, 0, rgdSamples, INPUT_SAMPLE_SIZE) # get channel 1 data

    #dwf.FDwfAnalogInStatusData(hdwf, 1, rgdSamples, 8192) # get channel 2 data


    dwf.FDwfAnalogInStatusData16(hdwf, 
                                 c_int(0),   # channel 1
                                 byref(big_output_buffer, big_output_pointer),
                                 0,
                                 INPUT_SAMPLE_SIZE
                                 )

    big_output_pointer += big_output_stride 


print('Number of loops: %d' % iTrigger)
print('Done...')
dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_bool(False))


# TODO are these 2 lines redundant?:
dwf.FDwfDeviceCloseAll()

# from AnalogOut_Pulse.py:
dwf.FDwfDeviceClose(hdwf)


#print_array(big_output_buffer)


print('full record time: %f sec' % BIG_BUFFER_FULL_TIME)
print('full record N samples: %d' % big_output_len) 
print('INPUT_SAMPLE_SIZE: %d (for 1 acquisition)' % INPUT_SAMPLE_SIZE)
print('INPUT_SAMPLE_RATE %f' % INPUT_SAMPLE_RATE )

approx_usb_bitrate = (16 * big_output_len) / BIG_BUFFER_FULL_TIME   # assuming data is transported as 2-byte values
print('approx USB bitrate: %f bits/sec' % approx_usb_bitrate)



pseudotimescale = INPUT_SAMPLE_PERIOD * np.arange(big_output_len)
# NOTE - this is ONLY considering the "small t" echo timescale; it DOES NOT account
# for the down time/delay between the end of an echo window and the next pulse
# e.g. for a 200usec (0.2ms) echo time and 10ms repetition time, 
# there is 9.8ms per of time (per repetition) that is "missing" from this scale and plot:


# TODO test this - pulse seems like only 2.5V not 5V??? 
# rescale int16 values to proper voltages:
voltage_signal = np.fromiter(big_output_buffer, dtype=float)    # TODO see also np.frombuffer - apparently ctypes -> numpy can be problematic.
voltage_signal = voltage_signal * SCOPE_VOLT_RANGE_CH1 / 65536 + SCOPE_VOLT_OFFSET_CH1


print('\n\n')
print('Scope Ch1 Recorded Stats:')
print('min voltage: %f (V)' % np.min(voltage_signal))
print('max voltage: %f (V)' % np.max(voltage_signal))

# plot int16 values against indexes
#plt.plot(big_output_buffer[:], '.-', label='Ch1 (int16)')    

# plot int16 values against pseudo-time
#plt.plot(pseudotimescale, big_output_buffer[:], '.-', label='Ch1 (int16)')

# plot proper voltages against indexes
#plt.plot(voltage_signal, '.-', label='Ch. 1 (V)')

# plot proper voltages against pseudo-time
plt.plot(pseudotimescale, voltage_signal, '.-', label='Ch. 1 (V)')

plt.title('%d Acq. @ %.2e Hz Sample Rate (%.2e s window)' % (WAVEGEN_N_ACQUISITIONS, INPUT_SAMPLE_RATE, INPUT_SINGLE_ACQUISITION_TIME))

#plt.xlabel('Index')
plt.xlabel('Seconds (TR delays not shown!)')

#plt.ylabel('int16 "voltage"')
plt.ylabel('Volts')
plt.legend()
#plt.xlim([0, 1000e-6])
plt.show()
