"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2018-07-19

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
import time
from dwfconstants import *
import sys
import matplotlib.pyplot as plt
import numpy as np
import math

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("Version: "+str(version.value))

cdevices = c_int()
dwf.FDwfEnum(c_int(0), byref(cdevices))
print("Number of Devices: "+str(cdevices.value))

if cdevices.value == 0:
    print("no device detected")
    quit()

print("Opening first device")
hdwf = c_int()
dwf.FDwfDeviceOpen(c_int(0), byref(hdwf))

if hdwf.value == hdwfNone.value:
    print("failed to open device")
    quit()

# print("Configure and start first analog out channel")
# dwf.FDwfAnalogOutEnableSet(hdwf, c_int(0), c_int(1)) # 1 = Sine wave")
# dwf.FDwfAnalogOutFunctionSet(hdwf, c_int(0), c_int(1))
# dwf.FDwfAnalogOutFrequencySet(hdwf, c_int(0), c_double(3000))
# dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_int(1))

#  creating waveform that we were using in the Waveforms software
# 1 MHz sine wave carrier frequency
# modulate with 5 us pulse
# repeat every 200 us
channelAcquire = c_int(0)
hzFreq = 3e3

# generate waveform samples
waveformSamples = (c_double*4096)()
# create buffer samples for one period of sine wave
timespots = np.linspace(0,1.0/3000,num=4096)
# wvsamples = []
index = 0
for t in timespots:
    waveformSamples[index] = math.sin(t*2*math.pi*3000)
    index = index+1
# plt.plot(waveformSamples)
# plt.title('wavesamples')
# plt.show()
print("Generating custom waveform...")

# settings for output
# dwf.FDwfAnalogOutEnableSet(hdwf, c_int(0), c_int(1)) # 1 = Sine wave")
dwf.FDwfAnalogOutNodeEnableSet(hdwf, c_int(0), AnalogOutNodeCarrier, c_bool(True))
dwf.FDwfAnalogOutNodeFunctionSet(hdwf, c_int(0), AnalogOutNodeCarrier, funcCustom)
dwf.FDwfAnalogOutNodeDataSet(hdwf, c_int(0), AnalogOutNodeCarrier, waveformSamples, c_int(4096))
# set 
dwf.FDwfAnalogOutNodeFrequencySet(hdwf, c_int(0), AnalogOutNodeCarrier, c_double(3000))
dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, c_int(0), AnalogOutNodeCarrier, c_double(2))

dwf.FDwfAnalogOutRunSet(hdwf, channelAcquire, c_double(20.0/hzFreq)) # run for 2 periods
dwf.FDwfAnalogOutWaitSet(hdwf, channelAcquire, c_double(1.0/hzFreq)) # wait one pulse time
dwf.FDwfAnalogOutRepeatSet(hdwf, channelAcquire, c_int(20)) # repeat 5 times

dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_bool(True))

print("Configure analog in")
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(1000000))
print("Set range for all channels")
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(-1), c_double(4))
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(1000))

print("Wait after first device opening the analog in offset to stabilize")
time.sleep(2)

print("Starting acquisition...")
dwf.FDwfAnalogInConfigure(hdwf, c_int(1), c_int(1))

sts = c_int()
while True:
    dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
    if sts.value == DwfStateDone.value :
        break
    time.sleep(0.1)
print("   done")

rg = (c_double*1000)()
dwf.FDwfAnalogInStatusData(hdwf, c_int(0), rg, len(rg)) # get channel 1 data
#dwf.FDwfAnalogInStatusData(hdwf, c_int(1), rg, len(rg)) # get channel 2 data

dwf.FDwfAnalogOutReset(hdwf, c_int(0))
dwf.FDwfDeviceCloseAll()

dc = sum(rg)/len(rg)
print("DC: "+str(dc)+"V")

plt.plot(np.fromiter(rg, dtype = np.float))
plt.show()

