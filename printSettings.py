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


# check which operating system is running
if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

hdwf = c_int()

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

whichconfig = c_int()
FDwfEnumConfigInfo(hdwf, byref(whichconfig))
print("config: {}".format(whichconfig))
