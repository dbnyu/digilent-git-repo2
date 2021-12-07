# Analog Discovery 2 Ultrasound Project

## Helper Functions
- see [ad2_tools.py](ad2_tools.py) for some wrapper/ helper functions for the Waveforms SDK (dwf) and ctypes variables
  - converting int16 -> double values
  - printing AD2 settings & errors
  - printing ctypes arrays

## Digilent Analog Discovery 2 Specs
- [Basic Specs & Pinout](https://digilent.com/reference/test-and-measurement/analog-discovery-2/specifications)
- [More Detailed Spec (including buffer sizes per internal instrument)](https://digilent.com/reference/test-and-measurement/analog-discovery-2/start)

### Bugs
- Make sure acquistion PC/laptop is *PLUGGED INTO POWER* during data acquisitions
  - Possible that some Windows/OS power-save functions reduce or disable USB communication when a laptop is on battery power (Dell Win10 laptop for example)
- **Use 50V as scope range** (even for a 5V signal). Apparently the AD2 only has 2 settings, 5 volts and 50 volts PEAK TO PEAK. So the 5V setting only allows +/-2.5V per this thread:
  - [2.7 Voltage cap on mesurements](https://forum.digilentinc.com/topic/20423-27-voltage-cap-on-mesurements/#comment-57671)

### Waveforms SDK
[Online HTML Manual](https://digilent.com/reference/software/waveforms/waveforms-sdk/reference-manual) - may be more stable than the PDF file...

#### Python ctypes & underlying C++ Pass-by-Reference
- [ctypes documentation](https://docs.python.org/3/library/ctypes.html)
  - [ctypes arrays & implicit creation](https://docs.python.org/3/library/ctypes.html#ctypes.Array)
    - "The recommended way to create concrete array types is by multiplying any ctypes data type with a positive integer." - this explains the confusing ```my_array = (c_double * 100)()``` syntax - it's an implicit ```ctypes``` Array constructor.
    - python ```len()``` should work; can also call the ```._length_``` and ```._type_``` fields for info.
- uses ```ctypes``` C-oriented datatypes and function calls
  - TODO how compatible is this with Numpy? Would a ```byref()``` call work w/ a numpy array as the output buffer?
- All function calls are pass-by-reference (== ctypes ```byref()```).
  - SDK documentation is not always clear when a scalar value is returned, vs. an array, since all pass-by-reference values are just pointers in the function definitions.
  - See the C++ ```dwf.h``` file - this has all the function prototypes/definitions, and specifies pass-by-reference array return sizes:
  - ```.../WaveFormsSDK/inc/dwf.h```

#### ctypes and Numpy arrays, file saving, etc.
- Much more convenient to do math & load/save files with Numpy arrays.
- Converting a ctypes buffer to Numpy needs to be handled carefully.
  - [Creating NumPy arrays from a ctypes pointer object is a problematic operation...](https://stackoverflow.com/questions/4355524/getting-data-from-ctypes-array-into-numpy)
- Digilent examples seem to use ```np.fromiter()```, but ```np.frombuffer()``` is also an options
  - seems that ```np.frombuffer()``` reads the same raw memory (RAM) as the original ctypes array
  - [frombuffer vs. fromstring](https://stackoverflow.com/questions/22236749/numpy-what-is-the-difference-between-frombuffer-and-fromstring) - ```np.fromstring()``` will make a copy in memory (e.g. 2x memory usage)



### USB Data Bandwidth & onboard Buffer Size

#### Onboard Memory Buffer
- the max buffer size for a single channel is 16k *samples*
  - scope & wavegen are 14-bit, but assuming data is stored/transported in full 2-Byte containers (TODO - TBD)
  - so 1 full buffer is 16k samples * 16 bits = 256,000 bits
- https://forum.digilentinc.com/topic/9171-is-there-an-sdk-interface-for-the-digitalin-voltage-thresholds/

#### USB Limitations
- [USB 2.0 limitations](https://forum.digilentinc.com/topic/18757-digilent-analog-discovery-2-record-mode-limiation/)
  - "The 480MHz is the USB 2.0 frequency, which uses some of this for sync and other usb protocol transfers, control... The maximum USB bulk IN bandwidth is about **40MBps, 370Mbps** for large data transfers. In the AD2 the bandwidth is **shared between various instruments**, so the **record is performed in small chunks which reduces the rate to about 1-2MHz**" (Attila - Digilent Engineer)

### AD2 Oscilloscope Voltage Range & int16 conversion
- https://forum.digilentinc.com/topic/20354-adc-bits-and-resolution/#comment-57297
- https://forum.digilentinc.com/topic/2340-how-to-switch-between-low-and-high-gain-on-inputs/
