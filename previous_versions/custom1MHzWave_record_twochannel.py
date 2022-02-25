"""
    use Digilent Analog Discovery 2 to output a custom waveform and record data to a csv file

    SDK can be found at C:\Program Files (x86)\Digilent\WaveFormsSDK

    Leanna Pancoast
"""

from ctypes import *
import time
import datetime
import os
from dwfconstants import *
import sys
import matplotlib.pyplot as plt
import numpy as np
import math
import csv

areaname = "transducers02"
folderPath = "C:\\Users\\pancol01\\Documents\\ultrasound\\testdoublerecord"

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
waveFreq = 1e6
# waveFreq = 0.5e6
wavePeriod = 1.0/waveFreq
waveBufferLen = 4096

fLost = 0
fCorrupted = 0
numLost = 0
numCorrupted = 0
numAvailable =[] 
arraynumcorrupted =[] 

# variables for input 
channelInput1 = c_int(0)
channelInput2 = c_int(1)
recordLength = c_double(1.0) # number of seconds
inputSampleFrequencyRaw = 2000000
inputSampleFrequency = c_double(inputSampleFrequencyRaw)
inputSamplePeriod = 1/inputSampleFrequencyRaw
inputVoltageRange = c_double(4)
inputBufferLength = c_int(int(recordLength.value*inputSampleFrequency.value))
sts = c_byte()

def main():
    initializeDevice()

    configureOutput()
    configureInput()

    # start output
    dwf.FDwfAnalogOutConfigure(hdwf, channelOutput, c_bool(True))

    # start acquisition engine and wait for stabilization
    print("Wait after first device opening the analog in offset to stabilize")
    time.sleep(2)

    recordedWave1,recordedWave2 = recordData()

    saveData(recordedWave1,recordedWave2)
    # plotData(recordedWave)


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
    # **** PLOT TO DOUBLE CHECK IF THE TIME FORM IS CORRECT ****
    # plt.plot(timespots,waveformSamples,marker='.')
    # plt.title('wavesamples at ' + str(waveFreq))
    # plt.show()
    print("Generating custom waveform...")

    # settings for output
    dwf.FDwfAnalogOutNodeEnableSet(hdwf, c_int(0), AnalogOutNodeCarrier, c_bool(True))
    dwf.FDwfAnalogOutNodeFunctionSet(hdwf, c_int(0), AnalogOutNodeCarrier, funcCustom)
    dwf.FDwfAnalogOutNodeDataSet(hdwf, c_int(0), AnalogOutNodeCarrier, waveformSamples, c_int(waveBufferLen))
    # set 
    dwf.FDwfAnalogOutNodeFrequencySet(hdwf, c_int(0), AnalogOutNodeCarrier, c_double(waveFreq))
    dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, c_int(0), AnalogOutNodeCarrier, c_double(2))

    # 40000 times to repeat is to be able to have it run for at least a few seconds
    timesToRepeat = c_int(40000)  # no unit
    pulseWidth = c_double(10e-6)  # in seconds
    pulseWait = c_double(190e-6)  # in seconds
    dwf.FDwfAnalogOutRunSet(hdwf, channelOutput, pulseWidth) 
    dwf.FDwfAnalogOutWaitSet(hdwf, channelOutput, pulseWait) 
    dwf.FDwfAnalogOutRepeatSet(hdwf, channelOutput, timesToRepeat) 



def configureInput():
    # inputSampleFrequency = c_double(100000)
    # +/- 2 V is 4 V range
    # inputVoltageRange = c_double(4)
    # inputBufferLength = c_int(1000)

    # setup acqusition
    dwf.FDwfAnalogInChannelEnableSet(hdwf, channelInput1, c_bool(True))
    dwf.FDwfAnalogInChannelRangeSet(hdwf, channelInput1, inputVoltageRange)
    dwf.FDwfAnalogInChannelEnableSet(hdwf, channelInput2, c_bool(True))
    dwf.FDwfAnalogInChannelRangeSet(hdwf, channelInput2, inputVoltageRange)

    dwf.FDwfAnalogInAcquisitionModeSet(hdwf, acqmodeRecord)
    dwf.FDwfAnalogInFrequencySet(hdwf, inputSampleFrequency)
    dwf.FDwfAnalogInRecordLengthSet(hdwf,recordLength)   # record for x seconds

    # print("Configure analog in")
    # dwf.FDwfAnalogInFrequencySet(hdwf, inputSampleFrequency)
    # print("Set range for all channels")
    # dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(-1), c_double(4))
    # dwf.FDwfAnalogInBufferSizeSet(hdwf, inputBufferLength)

def recordData():
    global fLost, fCorrupted, numLost, numCorrupted, numAvailable, arraynumcorrupted
    cSamples = 0
    cAvailable = c_int()
    cLost = c_int()
    cCorrupted = c_int()
    nSamples =  int(recordLength.value*inputSampleFrequency.value)
    rgdSamples1 = (c_double*nSamples)()
    rgdSamples2 = (c_double*nSamples)()

    print("Starting acquisition...")
    dwf.FDwfAnalogInConfigure(hdwf, c_int(1), c_int(1))

    while cSamples < nSamples:
        dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
        if cSamples == 0 and (sts == DwfStateConfig or sts == DwfStatePrefill or sts == DwfStateArmed) :
            # Acquisition not yet started.
            continue

        dwf.FDwfAnalogInStatusRecord(hdwf, byref(cAvailable), byref(cLost), byref(cCorrupted))
        numAvailable.append(cAvailable.value)
        arraynumcorrupted.append(cCorrupted.value)
        
        cSamples += cLost.value

        if cLost.value:
            fLost = 1
            numLost += cLost.value
        if cCorrupted.value:
            fCorrupted = 1
            numCorrupted += cCorrupted.value
        if cAvailable.value==0:
            continue

        if cSamples+cAvailable.value > nSamples:
            cAvailable = c_int(nSamples - cSamples)
        
        dwf.FDwfAnalogInStatusData(hdwf, channelInput1, byref( rgdSamples1, sizeof(c_double)*cSamples), cAvailable)
        dwf.FDwfAnalogInStatusData(hdwf, channelInput2, byref( rgdSamples2, sizeof(c_double)*cSamples), cAvailable)
        cSamples += cAvailable.value
    
    # deinitialize device
    dwf.FDwfAnalogOutReset(hdwf, channelOutput)
    dwf.FDwfDeviceCloseAll()
    return rgdSamples1,rgdSamples2

def saveData(myWave1, myWave2):
    print('savingData')
    currentTime = datetime.datetime.now().strftime("%Y%m%d-%Hh%Mm%Ss")

    data_filename = folderPath +'\\' + areaname + '_' + currentTime +'.csv' 
    flag_filename = folderPath +'\\' + areaname + '_' + currentTime +'_flags.txt' 
    available_filename = folderPath +'\\' + areaname + '_' + currentTime +'_available.txt' 

    with open(data_filename, 'w', newline='') as wave_file:
        wave_writer = csv.writer(wave_file, delimiter = ',')
        index = 0
        for x in myWave1:
            wave_writer.writerow([index,(index*inputSamplePeriod),x,myWave2[index]])
            index = index + 1
            if(index%1000==0):
                print('.',end='')
    print('\nfile written at' + data_filename)

    with open(flag_filename,'w',newline='') as flag_file:
        flag_file.write('flag corrupted:{}, numCorrupted: {}\n'.format(fCorrupted,numCorrupted))
        flag_file.write('flag lost: {}, numLost: {}'.format(fLost, numLost))
    print('\nfile written at' + flag_filename)

    with open(available_filename,'w',newline='') as available_file:
        for i in range(0,len(numAvailable)):
            available_file.write('{},{}\n'.format(numAvailable[i],arraynumcorrupted[i]))
    print('\nfile written at' + available_filename)

def plotData(myWave):
    outputTimespots = np.linspace(0,recordLength,num=inputSampleFrequencyRaw)
    plt.plot(outputTimespots,np.fromiter(myWave, dtype=float))
    plt.xlabel('seconds')
    plt.ylabel('voltage')
    plt.title('waveform recorded')
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