"""
    use Digilent Analog Discovery 2 to output a custom waveform and record data to a csv file

    SDK can be found at C:\Program Files (x86)\Digilent\WaveFormsSDK

    Leanna Pancoast
"""

from ctypes import *
import time
from dwfconstants import *
import sys
import matplotlib.pyplot as plt
import numpy as np
import math
import csv

# check which operating system is running
if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

hdwf = c_int()

# variables for output 
channelOutput = c_int(0)
waveFreq = 3e3
wavePeriod = 1.0/waveFreq
waveBufferLen = 4096

# variables for input 
channelInput = c_int(0)
recordLength = c_double(5.0) # number of seconds
inputSampleFrequency = c_double(100000)
inputVoltageRange = c_double(4)
inputBufferLength = c_int(int(recordLength.value*inputSampleFrequency.value))
sts = c_byte()

def main():
    initializeDevice()

    configureOutput()
    configureInput()

    # start output
    dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_bool(True))

    # start acquisition engine and wait for stabilization
    print("Wait after first device opening the analog in offset to stabilize")
    time.sleep(2)


    # sts = c_int()
    # while True:
    #     dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
    #     if sts.value == DwfStateDone.value :
    #         break
    #     time.sleep(0.1)
    # print("   done")

    # rg = (c_double*1000)()
    # dwf.FDwfAnalogInStatusData(hdwf, c_int(0), rg, len(rg)) # get channel 1 data

    recordedWave = recordData()

    plotData(recordedWave)

    # dc = sum(rg)/len(rg)
    # print("DC: "+str(dc)+"V")

    # plt.plot(np.fromiter(rg, dtype = float))
    # plt.show()

def configureOutput():
    # try to recreate the 3kHz wave that is in the other example, but with custom waveform
    # these values are set in global 
    # waveFreq = 3e3
    # wavePeriod = 1.0/waveFreq
    # waveBufferLen = 4096

    # generate waveform samples
    waveformSamples = (c_double*waveBufferLen)()
    # create buffer samples for one period of sine wave
    timespots = np.linspace(0,wavePeriod,num=waveBufferLen)
    index = 0
    for t in timespots:
        waveformSamples[index] = math.sin(t*2*math.pi*waveFreq)
        index = index+1
    # plt.plot(timespots,waveformSamples)
    # plt.title('wavesamples at ' + str(waveFreq))
    # plt.show()
    print("Generating custom waveform...")

    # settings for output
    # dwf.FDwfAnalogOutEnableSet(hdwf, c_int(0), c_int(1)) # 1 = Sine wave")
    dwf.FDwfAnalogOutNodeEnableSet(hdwf, c_int(0), AnalogOutNodeCarrier, c_bool(True))
    dwf.FDwfAnalogOutNodeFunctionSet(hdwf, c_int(0), AnalogOutNodeCarrier, funcCustom)
    dwf.FDwfAnalogOutNodeDataSet(hdwf, c_int(0), AnalogOutNodeCarrier, waveformSamples, c_int(waveBufferLen))
    # set 
    dwf.FDwfAnalogOutNodeFrequencySet(hdwf, c_int(0), AnalogOutNodeCarrier, c_double(waveFreq))
    dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, c_int(0), AnalogOutNodeCarrier, c_double(2))

    # timeToRun = c_double(10)
    timesToRepeat = c_int(715)
    dwf.FDwfAnalogOutRunSet(hdwf, channelOutput, c_double(20.0/waveFreq)) # run for x periods
    dwf.FDwfAnalogOutWaitSet(hdwf, channelOutput, c_double(1.0/waveFreq)) # wait one pulse time
    dwf.FDwfAnalogOutRepeatSet(hdwf, channelOutput, timesToRepeat) # repeat 5 times



def configureInput():
    # inputSampleFrequency = c_double(100000)
    # +/- 2 V is 4 V range
    # inputVoltageRange = c_double(4)
    # inputBufferLength = c_int(1000)

    # setup acqusition
    dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))
    dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(5))
    dwf.FDwfAnalogInAcquisitionModeSet(hdwf, acqmodeRecord)
    dwf.FDwfAnalogInFrequencySet(hdwf, inputSampleFrequency)
    dwf.FDwfAnalogInRecordLengthSet(hdwf,recordLength)   # record for 5 seconds

    # print("Configure analog in")
    # dwf.FDwfAnalogInFrequencySet(hdwf, inputSampleFrequency)
    # print("Set range for all channels")
    # dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(-1), c_double(4))
    # dwf.FDwfAnalogInBufferSizeSet(hdwf, inputBufferLength)

def recordData():
    cSamples = 0
    cAvailable = c_int()
    cLost = c_int()
    cCorrupted = c_int()
    fLost = 0
    fCorrupted = 0
    nSamples =  int(recordLength.value*inputSampleFrequency.value)
    rgdSamples = (c_double*nSamples)()

    print("Starting acquisition...")
    dwf.FDwfAnalogInConfigure(hdwf, c_int(1), c_int(1))

    while cSamples < nSamples:
        dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
        if cSamples == 0 and (sts == DwfStateConfig or sts == DwfStatePrefill or sts == DwfStateArmed) :
            # Acquisition not yet started.
            continue

        dwf.FDwfAnalogInStatusRecord(hdwf, byref(cAvailable), byref(cLost), byref(cCorrupted))
        
        cSamples += cLost.value
        
        if cLost.value:
            fLost = 1
        if cCorrupted.value:
            fCorrupted = 1
        
        if cAvailable.value==0:
            continue

        if cSamples+cAvailable.value > nSamples:
            cAvailable = c_int(nSamples - cSamples)
        
        dwf.FDwfAnalogInStatusData(hdwf, channelInput, byref( rgdSamples, sizeof(c_double)*cSamples), cAvailable)
        cSamples += cAvailable.value
    
    # deinitialize device
    dwf.FDwfAnalogOutReset(hdwf, c_int(0))
    dwf.FDwfDeviceCloseAll()
    return rgdSamples

def plotData(myWave):
    plt.plot(np.fromiter(myWave, dtype=float))
    with open('waverecord.csv', 'w', newline='') as wave_file:
        wave_writer = csv.writer(wave_file, delimiter = ',')
        index = 0
        for x in myWave:
            wave_writer.writerow([index,x])
            index = index + 1
    plt.show()


def initializeDevice():
    global hdwf
    # print out version number
    version = create_string_buffer(16)
    dwf.FDwfGetVersion(version)
    print("Version: "+str(version.value))

    # print out number of devices found on device
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


if __name__ == "__main__": 
    main() 