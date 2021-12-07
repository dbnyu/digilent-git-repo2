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


from ctypes import *
from dwfconstants import *
import matplotlib.pyplot as plt
import numpy as np
import sys
import time


nan = float('nan')  # for initializing variables

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



#def int16signal2voltage(data_int16, v_range, v_offset):
#    """Convert raw oscilloscope 16-bit int data back to proper voltages.
#
#        data_int16 = ctypes c_int16 array of samples (from one channel)
#        v_range = scope voltage range setting (float, volts)
#        v_offset = scope voltage offset setting (float, volts)
#
#        See Digilent Waveforms SDK documentation for FDwfAnalogInStatusData16 (page 21)
#
#        Returns a Numpy array of floats
#    """
#    # TODO - specify 32-bit or 64-bit floats for output? 64bit may be unnecessary if our range of values is only int16...
#    # TODO test this - pulse seems like only 2.5V not 5V??? 
#
#    # TODO maybe assuming v_offset = 0 is wrong - get it from the device!
#    # TODO 65536 is the range for an UNSIGNED int - so maybe we do need to offest to get proper +/- 5V (assuming that's the signal)
#
#    # TODO see also np.frombuffer - apparently ctypes -> numpy can be problematic.
#    voltage_signal = np.fromiter(acquisition_data_ch1, dtype=float)
#    voltage_signal = voltage_signal * v_range / 65536 + v_offset
#    return voltage_signal


def int16signal2voltage(hdwf, channel, data_int16):
    """Convert raw oscilloscope 16-bit int data back to proper voltages.

        hdwf = DWF object
        channel = 0 or 1; which channel is the data from? (to get the right range/offset)
                    This can be a regular Python int, ctypes not needed.
        data_int16 = ctypes c_int16 array of raw oscilloscope data

        Returns numpy array of floats/doubles.
    """
    v_range = c_double(nan)
    v_offset = c_double(nan)

    dwf.FDwfAnalogInChannelRangeGet(hdwf,  c_int(channel), byref(v_range))
    dwf.FDwfAnalogInChannelOffsetGet(hdwf, c_int(channel), byref(v_offset))

    print('int16 conversion range, offset: %f, %f (both volts)' % (v_range.value, v_offset.value))

    voltage_signal = np.fromiter(acquisition_data_ch1, dtype=float)
    voltage_signal = (voltage_signal * v_range.value / 65536) + v_offset.value
    return voltage_signal 


def print_scope_capabilities():
    """Print static info on the scope (ie. min/max possible voltage range)
        Things that are fixed in the hardware and not changeable at runtime.

        see also print_scope_settings() for querying changeable settings.
    """
    min_voltage_range = c_double()
    max_voltage_range = c_double()
    steps_voltage_range = c_double()
    
    dwf.FDwfAnalogInChannelRangeInfo(hdwf,
                                     byref(min_voltage_range),
                                     byref(max_voltage_range),
                                     byref(steps_voltage_range),
                                     )
    print('Scope Voltage Range Info:')
    print('min: %f' % min_voltage_range.value) 
    print('max: %f' % max_voltage_range.value)
    print('steps: %f' % steps_voltage_range.value)
    
    
    
    # Print out some info on the scope range/offset:
    min_voltage_offset = c_double()
    max_voltage_offset = c_double()
    steps_voltage_offset = c_double()
    
    dwf.FDwfAnalogInChannelOffsetInfo(hdwf, 
                                      byref(min_voltage_offset),
                                      byref(max_voltage_offset),
                                      byref(steps_voltage_offset)
                                      )

    print('Scope Voltage Offset Info:')
    print('min: %f' % min_voltage_offset.value) 
    print('max: %f' % max_voltage_offset.value)
    print('steps: %f' % steps_voltage_offset.value)


def print_scope_settings():
    """Access and print basic scope settings (User-changeable ones):

        For all channels:
            voltage range
            voltage offset

        See print_scope_capabilities for static variables.
    """

    # TODO is this working? getting all zeros for range/offset (range should be 5-25)

    ch1_current_v_range = c_double(float('nan'))
    ch2_current_v_range = c_double(float('nan'))
    
    ch1_current_v_offset = c_double(float('nan'))
    ch2_current_v_offset = c_double(float('nan'))
    
    
    dwf.FDwfAnalogInChannelRangeGet(hdwf, c_int(0), byref(ch1_current_v_range))
    dwf.FDwfAnalogInChannelRangeGet(hdwf, c_int(1), byref(ch2_current_v_range))
    
    dwf.FDwfAnalogInChannelOffsetGet(hdwf, c_int(0), byref(ch1_current_v_offset))
    dwf.FDwfAnalogInChannelOffsetGet(hdwf, c_int(1), byref(ch2_current_v_offset))
    print('Ch.1 v range, offset: %f, %f' % (ch1_current_v_range.value, ch1_current_v_offset.value))
    print('Ch.2 v range, offset: %f, %f' % (ch2_current_v_range.value, ch2_current_v_offset.value))

    
    ch1_attenuation = c_double(float('nan'))
    ch2_attenuation = c_double(float('nan'))

    dwf.FDwfAnalogInChannelAttenuationGet(hdwf, c_int(0), byref(ch1_attenuation))
    dwf.FDwfAnalogInChannelAttenuationGet(hdwf, c_int(1), byref(ch2_attenuation))
    print('Ch.1, Ch.2 Attenuation: %f, %f' % (ch1_attenuation.value, ch2_attenuation.value))



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

SCOPE_VOLT_RANGE_CH1 = 25.0      # oscilloscope ch1 input range (volts)
SCOPE_VOLT_OFFSET_CH1 = 0.      # oscilloscope ch1 offset (volts)  # TODO not yet implemented (only using for plotting atm.)

SCOPE_VOLT_RANGE_CH2 = 25.0      # ch2 - volts
SCOPE_VOLT_OFFSET_CH2 = 0.      # ch2 - volts   # TODO not yet implemented (only using for plotting atm.)

# TODO adjust voltage range for smaller echos? (ie. trigger-only channel can be 5V, but is scope more sensitive for echos if we use lower range? Or is this only for post-processing reconstruction of the voltage values?) 
# ie. does this have any bearing on the int16 values or not???

# TODO smarter input sanitizing/int casting here:

# internal recording parameters:
# for a single acquisition:
INPUT_SAMPLE_SIZE = int(INPUT_SAMPLE_RATE * INPUT_SINGLE_ACQUISITION_TIME)     # buffer size for 1 acquisition
INPUT_SAMPLE_PERIOD = 1. / INPUT_SAMPLE_RATE    # seconds per acquired sample


# NOTE - for now, ch 1 is the 'main recording channel' so only keeping track of ch1 status... assuming ch2. is 'in sync' with it, but we only care about the beginning of the ch2 signal anyway to see if the triggers/excitation pulses are in sync...
sts_ch1 = c_byte()  # scope channel 1 status



# number of samples for all repetitions (for 1 channel):
big_output_len = int(int(INPUT_SAMPLE_SIZE) * int(WAVEGEN_N_ACQUISITIONS))

# NOTE - we are recording int16 type samples; needs to be converted to voltage/double type in post-processing.
#big_output_buffer = (c_int16 * big_output_len)()
acquisition_data_ch1 = (c_int16 * big_output_len)()    # channel 1 main acquisition buffer (over full recording time)
acquisition_data_ch2 = (c_int16 * big_output_len)()    # channel 2 main acquisition buffer (over full recording time)

# troubleshooting: record double-formatted data too to check voltage computation:
double_data_ch1 = (c_double * big_output_len)()    # channel 1
double_data_ch2 = (c_double * big_output_len)()    # channel 2

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


print('\n\n')

print_scope_capabilities()
print()

print('User-Editable Settings (BEFORE):')
print_scope_settings()


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
# TODO are both scope channels started by the same single trigger???
# TODO can the 'global trigger bus' also use an external trigger (ie. MRI sync) to trigger BOTH the pulse and recording at the same time???
dwf.FDwfAnalogInTriggerAutoTimeoutSet(hdwf, c_double(0)) #disable auto trigger
dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcDetectorAnalogIn) #one of the analog in channels
dwf.FDwfAnalogInTriggerTypeSet(hdwf, trigtypeEdge)
dwf.FDwfAnalogInTriggerChannelSet(hdwf, c_int(0)) # first channel   # TODO set trigger/real acquisition channels to match Leanna's code
dwf.FDwfAnalogInTriggerLevelSet(hdwf, c_double(SCOPE_TRIGGER_VOLTAGE))
dwf.FDwfAnalogInTriggerConditionSet(hdwf, DwfTriggerSlopeRise) 


# TODO use ch2 trigger for ch1 AND ch2 acquisition
# TODO eventuallly if it's consistent/trustworth, maybe can ignore ch2 acquisition...
# TODO OR try to use a single transducer in duplex mode!!!

#or use trigger from other instruments or external trigger
#dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcExternal1) 
#dwf.FDwfAnalogInTriggerConditionSet(hdwf, DwfTriggerSlopeEither) 


print('\nScope Settings (AFTER setup):')
print_scope_settings()


print('\n')

# TODO does this start the actualy thing 
print("Starting repeated acquisitions")
dwf.FDwfAnalogInConfigure(hdwf, c_bool(False), c_bool(True))    # This starts the actual acquisition


print("Generating pulses")
dwf.FDwfAnalogOutConfigure(hdwf, channel, c_bool(True))     # this starts actual pulse output

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

# From AnalogIn_Trigger.py:
# TODO change name; itrigger is a vestige of one of the example files
for iTrigger in range(WAVEGEN_N_ACQUISITIONS):  # TODO this should be until big_buffer is filled (or N_acquistions)
    # new acquisition is started automatically after done state 

    #print('start loop %d' % iTrigger)
    #print('.', end='') # print a dot for every acquisition loop (comment out for faster loop)

    # busy wait loop for buffer to finish filling for 1 acquisition
    while True:
        dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts_ch1))
        # TODO - for now, using ch1. as the "main recording buffer" - so we only care if ch1 is finished, not ch2 (revisit this...)
        if sts_ch1.value == DwfStateDone.value:
            break
        #time.sleep(0.001) # TODO THIS SHOULD BE MUCH SMALLER O(1-10 microseconds)
        # TODO add this back in? or leave it? would be intersting to time this loop or count it especially at very high sample rates
    
    # TODO try capturing double-formatted data; see if the voltage values are correct there...

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
    dwf.FDwfAnalogInStatusData(hdwf, c_int(0), byref(double_data_ch1, double_ptr), INPUT_SAMPLE_SIZE)
    dwf.FDwfAnalogInStatusData(hdwf, c_int(1), byref(double_data_ch2, double_ptr), INPUT_SAMPLE_SIZE)

    acquisition_data_index += acquisition_data_stride 
    double_ptr += double_stride


print('Number of loops: %d' % iTrigger)
print('Done...')
dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_bool(False))


# TODO are these 2 lines redundant?:
dwf.FDwfDeviceCloseAll()

# from AnalogOut_Pulse.py:
dwf.FDwfDeviceClose(hdwf)


#print_array(acquisition_data_ch1)


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


# rescale raw int16 signals to proper voltages (float type):
#voltage_ch1 = int16signal2voltage(acquisition_data_ch1, SCOPE_VOLT_RANGE_CH1, SCOPE_VOLT_OFFSET_CH1);
#voltage_ch2 = int16signal2voltage(acquisition_data_ch2, SCOPE_VOLT_RANGE_CH2, SCOPE_VOLT_OFFSET_CH2);
# TODO test this - pulse seems like only 2.5V not 5V??? 

voltage_ch1 = int16signal2voltage(hdwf, 0, acquisition_data_ch1)
voltage_ch2 = int16signal2voltage(hdwf, 1, acquisition_data_ch2)



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
#   still, seems too good to be true??? TODO


print('\n\n')

# plot int16 values against indexes
#plt.plot(acquisition_data_ch1[:], '.-', label='Ch1 (int16)')    

# plot int16 values against pseudo-time
#plt.plot(pseudotimescale, acquisition_data_ch1[:], '.-', label='Ch1 (int16)')
#plt.plot(pseudotimescale, acquisition_data_ch2[:], '.-', label='Ch2 (int16)')

# plot proper voltages against indexes
#plt.plot(voltage_ch1, '.-', label='Ch. 1 (V)')

# plot proper voltages against pseudo-time
plt.plot(pseudotimescale, voltage_ch1, '.-', label='Ch. 1 (V)')
plt.plot(pseudotimescale, voltage_ch2, '.-', label='Ch. 2 (V)')

plt.title('%d Acq. @ %.2e Hz Sample Rate (%.2e s window)' % (WAVEGEN_N_ACQUISITIONS, INPUT_SAMPLE_RATE, INPUT_SINGLE_ACQUISITION_TIME))

#plt.xlabel('Index')
plt.xlabel('Seconds (TR delays not shown!)')

#plt.ylabel('int16 "voltage"')
plt.ylabel('Volts')
plt.legend()
#plt.xlim([0, 1000e-6])
plt.show()


#################
# Plot error:
plt.plot(difference, '.-', label='Ch2 - Ch1')
plt.title('Error @ %.2e Hz Sample Rate (%.2e s window)' % (INPUT_SAMPLE_RATE, INPUT_SINGLE_ACQUISITION_TIME))
plt.xlabel('Seconds (TR delays not shown!)')
plt.ylabel('Voltage')
plt.legend()
plt.show()





#################
# Troubleshooting voltage values:

err_ratio = np.divide(double_data_ch1, voltage_ch1)



plt.plot(pseudotimescale, voltage_ch1, '.-', label='int16 ch1')
plt.plot(pseudotimescale, double_data_ch1, '.-', label='double ch1')
plt.plot(pseudotimescale, err_ratio, '.-', label='err ratio')
plt.title('int16 voltage conversion vs. builtin double values')
plt.legend()
plt.xlabel('pseudotime')
plt.ylabel('Volts')
plt.show()

