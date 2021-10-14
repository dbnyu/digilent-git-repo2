# In the project directory, create a file called main.py and open in with a text editor.
# At th etop of the file, declare the imports like so:
from ctypes import *
from dwfconstants import *
import math
import time
import matplotlib.pyplot as plt, mpld3
import sys
import numpy
from io import BytesIO, StringIO
from flask import Flask, Response

# the dll must be loaded, and the method to do so depends on the operating system
if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

# THe next few lines of code declare some helper variables that are used
# to configure the Test and Measurement device. A sample buffer is also
# declared, which will soon be filled with data acquired from the device.

# declare ctype variables
hdwf = c_int()
sts = c_byte()
hzAcq = c_double(100000) # 100 kHz
nSamples = 200000
rgdSamples = (c_double*nSamples)()
cAvailable = c_int()
cLost = c_int()
cCorrupted = c_int()
fLost = 0
fCorrupted = 0

# Next the first available device is opened. The API returns a device
# handle that will be used to configure the device.

# open device
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

if hdwf.value == hdwfNone.value:
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    print("failed to open device")
    quit()

# the signal that is to be measured will come from the device itself
# It is configured to output a sine wave on the device's wavegen channel 1

# enable wavegen channel 1, set the waveform to sine, set the frequency
# to 1 Hz, the amplitude to 2V and start the wavegen
dwf.FDwfAnalogOutNodeEnableSet(hdwf, c_int(0), AnalogOutNodeCarrier, c_bool(True))
dwf.FDwfAnalogOutNodeFunctionSet(hdwf, c_int(0), AnalogOutNodeCarrier, funcSine)
dwf.FDwfAnalogOutNodeFrequencySet(hdwf, c_int(0), AnalogOutNodeCarrier, c_double(1))
dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, c_int(0), AnalogOutNodeCarrier, c_double(2))

# the device's oscilloscope channel is then configured to take samples,
# and is started

# enable scope channel 1, set the input range to 5v, set acquisition mode to record,
# set the sample frequency to 100kHz and set the record length to 2 seconds
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(5))
dwf.FDwfAnalogInAcquisitionModeSet(hdwf, acqmodeRecord)
dwf.FDwfAnalogInFrequencySet(hdwf, hzAcq)
dwf.FDwfAnalogInRecordLengthSet(hdwf, c_double(nSamples/hzAcq.value)) # -1 infinite record length

# wait at least 2 seconds for the offset to stabilize
time.sleep(2)

print("Starting oscilloscope")
dwf.FDwfAnalogInConfigure(hdwf, c_int(0), c_int(1))

cSamples = 0

while cSamples < nSamples:
    dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
    if cSamples == 0 and (sts == DwfStateConfig or sts == DwfStatePrefill or sts == DwfStateArmed):
        # Acquisition not yet started.
        continue

    # get the number of samples available, lost & corrupted
    dwf.FDwfAnalogInStatusRecord(hdwf, byref(cAvailable), byref(cLost), byref(cCorrupted))

    cSamples += cLost.value
    # set the lost and & corrupte flags
    if cLost.value:
        fLost = 1
    if cCorrupted.value:
        fCorrupted = 1
    
    # skip reading samples if there aren't any
    if cAvailable.value==0:
        continue

    # cap the available samples if the buffer would overflow
    # from what's really available
    if cSamples+cAvailable.value > nSamples:
        cAvailable = c_int(nSamples - cSamples)

    # read channel 1's available samples into the buffer
    dwf.FDwfAnalogInStatusData(hdwf, c_int(0), byref(rgdSamples, sizeof(c_double)))
    cSamples += cAvailable.value

# after taking samples it's good practice to cleanup by turning off
# the wavegen and closing the device

# reset the wavegen to stop it, close the device
dwf.FDwfAnalogOutReset(hdwf, c_int(0))
dwf.FDwfDeviceCloseAll()

# a graph image is created from the sampled data, with the image
# being kept in its own buffer to be used by the web server

# generate a graph image from the samples, and store it in a bytes buffer
plt.plot(numpy.fromiter(rgdSamples, dtype = numpy.float))
bio = BytesIO()
plt.savefig(bio, format="png")

# Finally a web server is setup to return the graph image whenver it gets a HTTP request

# start a web server, only if running as main
if __name__ == "__main__":
    app = Flask(__name__)

    @app.route('/')
    def root_handler():
        return Response(bio.getvalue(), mimetype = "image/png") # return the graph image in response

    app.run()