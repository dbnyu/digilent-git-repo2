"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2018-07-19

   Requires:                       
       Python 2.7, 3
   Desciption:
   - generates sine on AWG1
   - records data on Scope 1
   - writes data to 16 bit WAV file
"""

from ctypes import *
from dwfconstants import *
import math
import time
import matplotlib.pyplot as plt
import sys
import numpy
import wave
import datetime
import os
import array

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")


# Set output frequency, relative sampling frequency, and recording time:
# TODO sampling_factor > 8 seems to cause index error (rollover due to int16 type?) @ 200usec
output_freq = 1e6       # Hz
sampling_factor = 8     # mulitplier for sampling rate (eg. 2 for Nyquist)
sampling_time = 2    # time to record (seconds) - seems to work up to at least 10 sec. 


# (NOTE - files can be very large ~100MB w/ high sample rate and long duration...)



# some results w/ different parameters:

# Original: 80 Hz, 1000 samples/period, 10 periods
# TODO this interpretation can't be right... getting way more than 10 cycles...
#output_freq = 80            # frequency for waveform gen output
#sampling_factor = 1000      # multiply output_freq by this for acquisition sample rate (eg. Nyquist = 2)
#sampling_time = 10         # number of seconds to sample

#output_freq = 1e6
#sampling_factor = 2
#sampling_time = 10
# Output from above (1st try): - note samples corrupted!
# .\my_AnalogIn_Record_Wave_Mono001.py
# DWF Version: b'3.17.1'
# Opening first device
# Generating sine wave...
# Starting oscilloscope
# Generating 1000000.0Hz, recording 2000000.0Hz for 10.0s, press Ctrl+C to stop...
# Writing WAV file 'AD2_20211111_134604.wav'
#  done
#  Samples could be corrupted! Reduce frequency
#  Renaming file from 'AD2_20211111_134604.wav' to 'AD2_20211111_134604-134614.wav'
#   done

#output_freq = 1e6
#sampling_factor = 2
#sampling_time = 200e-6
#  Generating 1000000.0Hz, recording 2000000.0Hz for 0.0002s, press Ctrl+C to stop...
# seems to work?

# TODO sampling_factor > 8 seems to cause index error (rollover due to int16 type?) @ 200usec
#output_freq = 1e6       # Hz
#sampling_factor = 8     # mulitplier for sampling rate (eg. 2 for Nyquist)
#sampling_time = 5    # time to record (seconds) - seems to work up to at least 10 sec.

# 1Mhz/8x sampling, 1 sec:
# Generating 1000000.0Hz, recording 8000000.0Hz for 1.0s, press Ctrl+C to stop...
# Writing WAV file 'AD2_20211111_143550.wav'
#
# Try #2: 
# Generating 1000000.0Hz, recording 8000000.0Hz for 1.0s, press Ctrl+C to stop...
# Writing WAV file '20211111-145549-1.00e+06Mhz8x1.00e+00sec.wav'
# Loop count: 2805
#  done
#  Samples were lost! Reduce frequency
#  Samples could be corrupted! Reduce frequency
#   done




#declare ctype variables
hdwf = c_int()
sts = c_byte()
vOffset = c_double(1.41)
vAmplitude = c_double(1.41)
#hzSignal = c_double(80)    # see above for setting frequency/sample rate/record time.
#hzAcq = c_double(80000)
#nSamples = 800000
hzSignal = c_double(output_freq)
hzAcq = c_double(output_freq * sampling_factor)
nSamples = int(output_freq * sampling_factor * sampling_time) # avoiding ctypes math here

cAvailable = c_int()
cLost = c_int()
cCorrupted = c_int()
fLost = 0
fCorrupted = 0

#print(DWF version
version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

#open device
print("Opening first device")
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

if hdwf.value == hdwfNone.value:
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    print("failed to open device")
    quit()


# looking for memory config options:
pnSamplesMin = c_int()
pnSamplesMax = c_double()
print('Before:')
print('pnSamplesMin: ', pnSamplesMin)
print('pnSamplesMax: ', pnSamplesMax)
dwf.FDwfAnalogOutNodeDataInfo(hdwf, c_int(0), AnalogOutNodeCarrier, byref(pnSamplesMin), byref(pnSamplesMax)) 
print('After:')
print('pnSamplesMin: ', pnSamplesMin)
print('pnSamplesMax: ', pnSamplesMax)

# TODO chapter 9.2 Configuration...
#FDwfDigitalInInternalClockInfo(HDWF hdwf, double *phzFreq)

print("Generating sine wave...")
dwf.FDwfAnalogOutNodeEnableSet(hdwf, c_int(0), AnalogOutNodeCarrier, c_bool(True))
dwf.FDwfAnalogOutNodeFunctionSet(hdwf, c_int(0), AnalogOutNodeCarrier, funcSine)
dwf.FDwfAnalogOutNodeFrequencySet(hdwf, c_int(0), AnalogOutNodeCarrier, hzSignal)
dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, c_int(0), AnalogOutNodeCarrier, vAmplitude)
dwf.FDwfAnalogOutNodeOffsetSet(hdwf, c_int(0), AnalogOutNodeCarrier, vOffset)
dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_bool(True))

#set up acquisition
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(2.0*vAmplitude.value))
dwf.FDwfAnalogInChannelOffsetSet(hdwf, c_int(0), vOffset)
dwf.FDwfAnalogInAcquisitionModeSet(hdwf, acqmodeRecord)
dwf.FDwfAnalogInFrequencySet(hdwf, hzAcq)
dwf.FDwfAnalogInRecordLengthSet(hdwf, c_double(-1)) # -1 infinite record length

#wait at least 2 seconds for the offset to stabilize
print("2 sec Delay for warmup...")
time.sleep(2)

print("Starting oscilloscope")
dwf.FDwfAnalogInConfigure(hdwf, c_int(0), c_int(1))

cSamples = 0

print("Generating "+str(hzSignal.value)+"Hz, recording "+str(hzAcq.value)+"Hz for "+str(nSamples/hzAcq.value)+"s, press Ctrl+C to stop...");
#get the proper file name

#open WAV file
starttime = datetime.datetime.now();
startfilename = "%s-%.2eMhz%dx%.2esec" % (starttime.strftime("%Y%m%d-%H%M%S"), output_freq, sampling_factor, sampling_time)
startfilename = startfilename.replace('.', 'p') # replace decimals with 'p' character
startfilename = startfilename + ".wav"

#startfilename = "AD2_" + "{:04d}".format(starttime.year) + "{:02d}".format(starttime.month) + "{:02d}".format(starttime.day) + "_" + "{:02d}".format(starttime.hour) + "{:02d}".format(starttime.minute) + "{:02d}".format(starttime.second) + ".wav";
print("Writing WAV file '" + startfilename + "'");
waveWrite = wave.open(startfilename, "wb");
waveWrite.setnchannels(1);				# 1 channels 
waveWrite.setsampwidth(2);				# 16 bit / sample
waveWrite.setframerate(hzAcq.value);
waveWrite.setcomptype("NONE","No compression");


# time the actual loop
loop_timer = datetime.datetime.now()

try:
    loop_count = 0
    while cSamples < nSamples:
        dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
        if cSamples == 0 and (sts == DwfStateConfig or sts == DwfStatePrefill or sts == DwfStateArmed) :
            # Acquisition not yet started.
            # TODO maybe could make this a separate loop to avoid 'if' statement in main loop...
            continue

        dwf.FDwfAnalogInStatusRecord(hdwf, byref(cAvailable), byref(cLost), byref(cCorrupted))
        
        cSamples += cLost.value



        # trying to avoid 'if' branches - addition should be a little faster in tight loop. 
        fLost += cLost.value
        fCorrupted += cCorrupted.value

        #if cLost.value :
        #    fLost = 1
        #if cCorrupted.value :
        #    fCorrupted = 1




        if cAvailable.value==0 :        # TODO maybe change this to <= 0? (that won't fix the negative index but might prevent crash?)
            continue

        if cSamples+cAvailable.value > nSamples :
            cAvailable = c_int(nSamples-cSamples)

        # TODO delete all print statements (loop timing!)
        #print("Loop count: %d" % loop_count)
        #print('cLost.value: ', cLost.value)
        #print('cCorrupted.value: ', cCorrupted.value)
        #
        #print('type(cAvail): ', type(cAvailable))
        #print('type(cAvail.value): ', type(cAvailable.value))
        #print('cAvail: ', cAvailable.value)
        
        rgSamples = (c_int16*cAvailable.value)()    # TODO this becomes negative w/ sample rate > 8MHz - maybe overflowing int16 max value?


        dwf.FDwfAnalogInStatusData16(hdwf, c_int(0), rgSamples, c_int(0), cAvailable) # get channel 1 data chunk
        cSamples += cAvailable.value
        waveWrite.writeframes(rgSamples)

        loop_count = loop_count + 1
        
except KeyboardInterrupt:
    pass	

# time the actual loop
loop_timer = datetime.datetime.now() - loop_timer

print('\n')
print("Loop count: %d" % loop_count)
print("Loop time : %s" % str(loop_timer))
print('\n')


#endtime = datetime.datetime.now();
dwf.FDwfAnalogOutReset(hdwf, c_int(0))
dwf.FDwfDeviceCloseAll()

print(" done")


# percentage lost/corrupted:
lost_pct = 100. * (float(fLost) / nSamples)
corrupted_pct = 100. * (float(fCorrupted) / nSamples)


if fLost:
    print("%d Samples were lost! Reduce frequency (%.2f%%)" % (fLost, lost_pct))
if fCorrupted:
    print("%d Samples could be corrupted! Reduce frequency (%.2f%%)" % (fCorrupted, corrupted_pct))

waveWrite.close();

#endfilename = "AD2_" + "{:04d}".format(starttime.year) + "{:02d}".format(starttime.month) + "{:02d}".format(starttime.day) + "_" + "{:02d}".format(starttime.hour) + "{:02d}".format(starttime.minute) + "{:02d}".format(starttime.second) + "-" + "{:02d}".format(endtime.hour) + "{:02d}".format(endtime.minute) + "{:02d}".format(endtime.second) + ".wav";
#print("Renaming file from '" + startfilename + "' to '" + endfilename + "'");
#os.rename(startfilename, endfilename);

print(" done")

