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

    Using AnalogOut_Pulse.py
    and
    AnalogIn_Trigger.py

    Doug Brantner 12/2/2021
"""


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

# TODO - try the 

# TODO - from AnalogIn_Record_Trigger_int16.py:
#        plt.plot(numpy.fromiter(rgSamples1, dtype = numpy.int16))
#        fromiter specifying CORRECT originating datatype...

        



from ctypes import *
from dwfconstants import *
import matplotlib.pyplot as plt
import numpy as np
import sys
import time
import ad2_tools as ad2       # my library


#nan = float('nan')  # for initializing variables

# TODO look at AnalogInDigitalIn_Acquisition.py for trigger sync between analog/digital inputs...






# Adding temp save data from custom1MHzWave_record_twochannel_16bit.py:

import datetime
import os
import csv
areaname = "inUSgel_lgBUF_4milSample_lessarr"
#folderPath = "C:\\Users\\pancol01\\Documents\\ultrasound\\testdoublerecord"
folderPath = '2021-12-08-phantomTests'

def saveData(myWave1, myWave2):
    """ from custom1MHzWave_record_twochannel_16bit.py"""

    print('savingData')
    currentTime = datetime.datetime.now().strftime("%Y%m%d-%Hh%Mm%Ss")

    data_filename = folderPath +'\\' + areaname + '_' + currentTime +'.csv' 
    flag_filename = folderPath +'\\' + areaname + '_' + currentTime +'_flags.txt' 
    available_filename = folderPath +'\\' + areaname + '_' + currentTime +'_available.txt' 

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



# Pulser Parameters (Wavegen Output #1):
# This is for a single positive-going rectangular pulse, that is repeated every 'wait time'
# WAVEGEN_N_ACQUISITIONS sets the number of pulses generated, which also determines the number of acquisitions (and run time)
# User Editable:
WAVEGEN_N_ACQUISITIONS = 10        # number of pulse/echo repetitions to acquire
WAVEGEN_WAIT_TIME = 0.01            # seconds between acquisiztions (== TR period, also serves as trigger/acquisition interval)
WAVEGEN_PULSE_WIDTH = 0.5e-6          # pulse width in seconds (???) TODO CHECK THIS (confirm w/ scope)
# TODO should pulse width be 1/2 usec?
WAVEGEN_PULSE_AMPLITUDE = 5.0       # voltage for pulse
WAVEGEN_PULSE_V_OFFSET  = 0.        # voltage offset for pulse

# Recording Parameters:
# From AnalogIn_Trigger.py
# User Editable:
# NOTE: AD2 will limit sample rates > 100Mhz without any warning.
INPUT_SAMPLE_RATE = 10e6      # Hz 
INPUT_SINGLE_ACQUISITION_TIME = 200e-6        # time to record a single echo (seconds)
INPUT_TRIGGER_POSITION_TIME = 0.99 * 0.5 * INPUT_SINGLE_ACQUISITION_TIME  # seconds, trigger position within the acquisition window; default is center (t=0) which wastes 1/2 the buffer
#       0.5 * acq_time = move trigger to beginning of acquisition window 
#               - so that trigger instant is the first sample
#       0.99 * above = allow 1usec of dead time "pre-roll" before trigger
#               - so that we can see 1 pulse period of "intentional nothing" before trigger/pulse
#                   so we can be sure the triggers are perfectly in sync (ie. ensure we capture the correct rising edge)
#               - 0.99 assumes 200usec window so that 1/2 is 100usec and 99% of 100 == 99usec, so there is 1usec of dead pre-roll time in the beginning.

SCOPE_TRIGGER_VOLTAGE = 1.0     # volts, threshold to start acquisition

SCOPE_VOLT_RANGE_CH1 = 50.0      # oscilloscope ch1 input range (volts)
SCOPE_VOLT_OFFSET_CH1 = 0.      # oscilloscope ch1 offset (volts)  # TODO not yet implemented (only using for plotting atm.)

SCOPE_VOLT_RANGE_CH2 = 5.0      # ch2 - volts
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
#double_data_ch1 = (c_double * big_output_len)()    # channel 1
#double_data_ch2 = (c_double * big_output_len)()    # channel 2

#print_array(big_output_buffer, 0)


# TODO double check these:
BIG_BUFFER_FULL_TIME = big_output_len * INPUT_SINGLE_ACQUISITION_TIME     # this does NOT include dead time between repetitions! 
print('full record time: %f sec' % BIG_BUFFER_FULL_TIME)

total_record_time = WAVEGEN_N_ACQUISITIONS * WAVEGEN_WAIT_TIME  # just for reference


if INPUT_SAMPLE_RATE > 100e6:
    print('WARNING: sample rates > 1Mhz not supported by Digilent AD2 device!')
    # TODO limit here so plots don't show erroneous high acquisition frequencies?



print('Acquiring %d periods over %.2f seconds...' %  (WAVEGEN_N_ACQUISITIONS, total_record_time))


dwf = ad2.load_dwf()
#if sys.platform.startswith("win"):
#    dwf = cdll.dwf
#elif sys.platform.startswith("darwin"):
#    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
#else:
#    dwf = cdll.LoadLibrary("libdwf.so")

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

print('testing my error function:')
print(ad2.get_error(dwf) + '\n')

# the device will be configured only when calling FDwfAnalogOutConfigure
dwf.FDwfDeviceAutoConfigureSet(hdwf, c_int(0))


print('\n\n')

ad2.print_scope_capabilities(dwf, hdwf)
print()

print('User-Editable Settings (BEFORE):')
ad2.print_scope_settings(dwf, hdwf)


# Wavegen Output
# from AnalogOut_Pulse.py:

# TODO break out important settings to user-edit section up top (amplitude, etc)

# Single Square Wave Pulse:
dwf.FDwfAnalogOutNodeEnableSet(hdwf, channel, AnalogOutNodeCarrier, c_bool(True))
dwf.FDwfAnalogOutIdleSet(hdwf, channel, DwfAnalogOutIdleOffset)
dwf.FDwfAnalogOutNodeFunctionSet(hdwf, channel, AnalogOutNodeCarrier, funcSquare)
dwf.FDwfAnalogOutNodeFrequencySet(hdwf, channel, AnalogOutNodeCarrier, c_double(0)) # low frequency
dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, AnalogOutNodeCarrier, c_double(WAVEGEN_PULSE_AMPLITUDE))
#dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, AnalogOutNodeCarrier, c_double(-5))    # TODO not clear if negative square amplitude is valid? probalby not..
dwf.FDwfAnalogOutNodeOffsetSet(hdwf, channel, AnalogOutNodeCarrier, c_double(WAVEGEN_PULSE_V_OFFSET))
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


print('\nScope Settings (AFTER setup):')
ad2.print_scope_settings(dwf, hdwf)


print('\n')

# TODO does this start the actualy thing 
print("Starting repeated acquisitions")
dwf.FDwfAnalogInConfigure(hdwf, c_bool(False), c_bool(True))    # This starts the actual acquisition


print('\nScope Settings (AFTER configure):')
ad2.print_scope_settings(dwf, hdwf)

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
    #dwf.FDwfAnalogInStatusData(hdwf, c_int(0), byref(double_data_ch1, double_ptr), INPUT_SAMPLE_SIZE)
    #dwf.FDwfAnalogInStatusData(hdwf, c_int(1), byref(double_data_ch2, double_ptr), INPUT_SAMPLE_SIZE)

    acquisition_data_index += acquisition_data_stride 
    double_ptr += double_stride


print('Number of loops: %d' % iTrigger)
print('Done...')
dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_bool(False))
# TODO close the scope too?


print('int16 ch1 min: %d' % min(acquisition_data_ch1))
print('int16 ch1 max: %d' % max(acquisition_data_ch1))


# need to do this BEFORE closing the scope because the scope range/offset calls are required
# TODO could just store those & use later...
voltage_ch1 = ad2.int16signal2voltage(dwf, hdwf, 0, acquisition_data_ch1)
voltage_ch2 = ad2.int16signal2voltage(dwf, hdwf, 1, acquisition_data_ch2)

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

# TEMP DELETE THIS TODO
# plot int16 values against pseudo-time
#plt.plot(pseudotimescale, acquisition_data_ch1[:], '.-', label='Ch1 (int16)')
#plt.plot(pseudotimescale, acquisition_data_ch2[:], '.-', label='Ch2 (int16)')
#plt.xlabel('Index')
#plt.ylabel('int16 "voltage"')
#plt.legend()
#plt.show()
#sys.exit()


# rescale raw int16 signals to proper voltages (float type):
#voltage_ch1 = int16signal2voltage(acquisition_data_ch1, SCOPE_VOLT_RANGE_CH1, SCOPE_VOLT_OFFSET_CH1);
#voltage_ch2 = int16signal2voltage(acquisition_data_ch2, SCOPE_VOLT_RANGE_CH2, SCOPE_VOLT_OFFSET_CH2);
# TODO test this - pulse seems like only 2.5V not 5V??? 

# NOTE - if calling voltage range/offset, need to do this BEFORE closing the hdwf device!!!
#voltage_ch1 = ad2.int16signal2voltage(dwf, hdwf, 0, acquisition_data_ch1, v_range=5, v_offset=0)
#voltage_ch2 = ad2.int16signal2voltage(dwf, hdwf, 1, acquisition_data_ch2, v_range=5, v_offset=0)

# moved to library:
#voltage_ch1 = int16signal2voltage(hdwf, 0, acquisition_data_ch1)
#voltage_ch2 = int16signal2voltage(hdwf, 1, acquisition_data_ch2)




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
# Bland-Altman of ch1 vs. ch2
ad2.bland_altman(voltage_ch1, voltage_ch2)


# saving 16bit data: 
print('Saving raw int16 data...')
saveData(acquisition_data_ch1, acquisition_data_ch2)

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
