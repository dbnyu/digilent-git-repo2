"""Single Pulse repeated & using 2nd scope as trigger for windowed acquisition.

    Using AnalogOut_Pulse.py
    and
    AnalogIn_Trigger.py

    Doug Brantner 12/2/2021
"""

# Wavegen Output
# from AnalogOut_Pulse.py:

from ctypes import *
from dwfconstants import *
import matplotlib.pyplot as plt
import sys
import time

# TODO look at AnalogInDigitalIn_Acquisition.py for trigger sync between analog/digital inputs...

def print_array(arr, line_len=10):
    """print an array horizontally.
    
    arr = ctypes array
    line_len = print a newline after this many entries; set to zero or None to print 1 line
    """

    for i in range(len(arr)):
        print(str(arr[i]) + ',', end='')

        if line_len > 0  and (i+1) % line_len == 0: # i+1 because of zero based index?
            print()




# Pulser Parameters (Wavegen Output #1):
# User Editable:
N_acquisitions = 100;   # number of pulse/echo repetitions to acquire
wait_time = 0.01;       # seconds between acquisiztions (== TR period)
pulse_width = 1e-6      # pulse width in seconds (???) TODO CHECK THIS
# TODO should pulse width be 1/2 usec?


# Recording Parameters:
# From AnalogIn_Trigger.py
# User Editable:
INPUT_SAMPLE_RATE = 4e6         # Hz
INPUT_ECHO_TIME = 200e-6        # time to record a single echo (seconds)
# TODO change to "single acquisition time"
TRIGGER_VOLTAGE = 1.0           # volts


# TODO smarter input sanitizing/int casting here:

# internal recording parameters:
# for a single acquisition:
INPUT_SAMPLE_SIZE = int(INPUT_SAMPLE_RATE * INPUT_ECHO_TIME)     # buffer size for 1 acquisition
sts = c_byte()
#rgdSamples = (c_double*8192)()   # TODO adjust this to final output buffer size (?)


#rgSamples1 = (c_int16*INPUT_SAMPLE_SIZE)()  # allocate output array for ch 1

big_output_len = int(int(INPUT_SAMPLE_SIZE) * int(N_acquisitions))
big_output_buffer = (c_int16 * big_output_len)()
#big_output_buffer = (100 * c_int16)()
#print_array(big_output_buffer, 0)
#big_output_buffer.contents.size
#sys.exit()

BIG_BUFFER_FULL_TIME = big_output_len * INPUT_ECHO_TIME
print('full record time: %f sec' % BIG_BUFFER_FULL_TIME)

total_record_time = N_acquisitions * wait_time  # just for reference


print('Acquiring %d periods over %.2f seconds...' %  (N_acquisitions, total_record_time))



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



# Single Square Wave Pulse:
dwf.FDwfAnalogOutNodeEnableSet(hdwf, channel, AnalogOutNodeCarrier, c_bool(True))
dwf.FDwfAnalogOutIdleSet(hdwf, channel, DwfAnalogOutIdleOffset)
dwf.FDwfAnalogOutNodeFunctionSet(hdwf, channel, AnalogOutNodeCarrier, funcSquare)
dwf.FDwfAnalogOutNodeFrequencySet(hdwf, channel, AnalogOutNodeCarrier, c_double(0)) # low frequency
dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, AnalogOutNodeCarrier, c_double(5))
#dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, AnalogOutNodeCarrier, c_double(-5))    # TODO not clear if negative square amplitude is valid? probalby not..
dwf.FDwfAnalogOutNodeOffsetSet(hdwf, channel, AnalogOutNodeCarrier, c_double(0))
dwf.FDwfAnalogOutRunSet(hdwf, channel, c_double(pulse_width)) # pulse length in time (?)
dwf.FDwfAnalogOutWaitSet(hdwf, channel, c_double(wait_time)) # wait length  10 ms = 100 Hz repetition frequency (TR)
#dwf.FDwfAnalogOutWaitSet(hdwf, channel, c_double(2e-6)) # wait length
dwf.FDwfAnalogOutRepeatSet(hdwf, channel, c_int(N_acquisitions)) # repeat N times
# TODO count # of pulses (i.e. small number like 10)
# TODO see if square wave can go +/- or only +????




# TODO is this gonna work? multiple pings are happenings automatically now (already started)
# but we need to read in a loop...
# TODO may need a TR counter or a timeout (ie. if we lose some pings, when do we stop?)
# TODO is there a wavegen off trigger? ie. when the automatic pulse train stops????

# TODO could just use a continuous square wave/sine packet and count TR's... maybe ...Pulse is not the right thing to use?
# TODO waht about a digital pin as the timer/trigger (which can then be replaced w/ an MRI trigger when the time comes...?)




# From AnalogIn_Trigger.py
#set up acquisition
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(INPUT_SAMPLE_RATE))
#dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(8192))    # TODO adjust to single echo size (?)
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(INPUT_SAMPLE_SIZE))
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))
# TODO enable channel 2 also? (YES need to enable separately) - look at dualrecord (Leanna)
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(5))    # TODO adjust voltage range for smaller echos?
# TODO channelrangeset for ch2
# TODO does this matter if using raw 16bit inputs?



#set up trigger
dwf.FDwfAnalogInTriggerAutoTimeoutSet(hdwf, c_double(0)) #disable auto trigger
dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcDetectorAnalogIn) #one of the analog in channels
dwf.FDwfAnalogInTriggerTypeSet(hdwf, trigtypeEdge)
dwf.FDwfAnalogInTriggerChannelSet(hdwf, c_int(0)) # first channel
dwf.FDwfAnalogInTriggerLevelSet(hdwf, c_double(TRIGGER_VOLTAGE))
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

# TODO figure out analogin trigger timeout (see p.34 of docs)


big_output_pointer = 0  # pointer into big_output_buffer to write full (single) acquisition blocks
big_output_stride = INPUT_SAMPLE_SIZE * sizeof(c_int16)


for iTrigger in range(N_acquisitions):  # TODO this should be until big_buffer is filled (or N_acquistions)
    # new acquisition is started automatically after done state 

    print('start loop %d' % iTrigger)

    # busy wait loop for buffer to finish filling for 1 acquisition
    while True:
        dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
        if sts.value == DwfStateDone.value :
            break
        #time.sleep(0.001) # TODO THIS SHOULD BE MUCH SMALLER O(1-10 microseconds)
    
    #dwf.FDwfAnalogInStatusData(hdwf, 0, rgdSamples, 8192) # get channel 1 data
    #dwf.FDwfAnalogInStatusData(hdwf, 0, rgdSamples, INPUT_SAMPLE_SIZE) # get channel 1 data

    #dwf.FDwfAnalogInStatusData(hdwf, 1, rgdSamples, 8192) # get channel 2 data


    # TODO START HERE - look at AnalogIn_Record_int16.py
    #dwf.FDwfAnalogInStatusData16(hdwf, 
    #                            c_int(0),   # channel 1
    #                            byref(rgSamples1, sizeof(c_int16)*iSample), 
    #                            c_int(iBuffer), 
    #                            c_int(cSamples)) # get channel 1 data
    dwf.FDwfAnalogInStatusData16(hdwf, 
                                 c_int(0),   # channel 1
                                 byref(big_output_buffer, big_output_pointer),
                                 0,
                                 INPUT_SAMPLE_SIZE
                                 )

    # TODO copy to output buffer    (can that be done byreference in the line 168 call???
    
    #dc = sum(rgdSamples)/len(rgdSamples)
    #print("Acquisition #"+str(iTrigger)+" average: "+str(dc)+"V")

    big_output_pointer += big_output_stride 


print('Number of loops: %d' % iTrigger)
print('Done...')
dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_bool(False))
dwf.FDwfDeviceCloseAll()






# from AnalogOut_Pulse.py:
dwf.FDwfDeviceClose(hdwf)


#print(big_output_buffer)
#print_array(big_output_buffer)


print('full record time: %f sec' % BIG_BUFFER_FULL_TIME)
print('full record N samples: %d' % big_output_len) 
print('INPUT_SAMPLE_SIZE: %d' % INPUT_SAMPLE_SIZE)
print('INPUT_SAMPLE_RATE %f' % INPUT_SAMPLE_RATE )

plt.plot(big_output_buffer[:], '.-', label='bigbuffer')
plt.xlabel('Index')
plt.ylabel('int16 "voltage"')
plt.legend()
plt.show()
