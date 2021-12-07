"""Helper Functions for Digilent Analog Discovery 2.

    Requires Waveforms and Waveforms SDK.
    Requires ctypes
    Requires Numpy

    The 'hdfw' object should be initialized & passed from the calling program.

    Doug Brantner 12/7/2021
"""


from ctypes import *
#from dwfconstants import *
import numpy as np
import sys

# contstants

NAN = float('nan')      # for initializing test values


def load_dwf():
    """Find and load platform-specific DWF (Waveforms SDK) library.

        from Digilent example code.

        Returns dwf object.
    """

    if sys.platform.startswith("win"):
        dwf = cdll.dwf
    elif sys.platform.startswith("darwin"):
        dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
    else:
        dwf = cdll.LoadLibrary("libdwf.so")

    return dwf



def get_error(dwf):
    """Get error message & print it from Analog Discovery 2.

        Returns error as a string.
    """
    szError = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szError);
    return str(szError.value)

def check_and_print_error(dwf, throw=False):
    """Wrapper for get_error.

        dwf = DWF object
        throw = optionally raise a Python exception
    """

    # TODO incorporate 'logging' module...

    err_str = get_error(dwf)

    if len(err_str) > 0:    # TODO make this work for ctypes converted string...
    #if err_str[0] != b'\0':
    #if err_str[0] != 0x00:
        print('firstchar = %x' % ord(err_str[0]))
        s = 'DWF ERROR: %s' % err_str
        print(s)

        if throw:
            raise(RuntimeError, s)


def int16signal2voltage(dwf, hdwf, channel, data_int16, v_range=None, v_offset=None):
    """Convert raw oscilloscope 16-bit int data back to proper voltages.


        dwf = DLL library (see load_dwf() above.)
        hdwf = c_int, initialized hardware device handle (???)
        channel = 0 or 1; which channel is the data from? 
                    (to get the right range/offset values)
                    This can be a regular Python int, ctypes not needed.
        data_int16 = ctypes c_int16 array of raw oscilloscope data

        v_range = scope voltage range (optional)
        v_offset = scope voltage offset (optional)
            These can both be passed as regular Python floats and will be
            cast to ctypes c_double internally here.

        Returns numpy array of floats/doubles.
    """

    # TODO - why is this not working??? - the NaN's used as initial values are not getting overwritten...

    # initialize with NaN's so we know if it's updated properly
    if v_range is None:
        v_range = c_double(NAN) 
        dwf.FDwfAnalogInChannelRangeGet(hdwf, c_int(channel), byref(v_range))
        check_and_print_error(dwf)
        #print(get_error(dwf))
    else:
        v_range = c_double(v_range) 


    if v_offset is None:
        v_offset = c_double(NAN)
        dwf.FDwfAnalogInChannelOffsetGet(hdwf, c_int(channel), byref(v_offset))
        check_and_print_error(dwf)
        #print(get_error(dwf))
    else:
        v_offset = c_double(v_offset) 

    print('int16 conversion range, offset: %f, %f (both volts)' % (v_range.value, v_offset.value))
    print('Raw int16 min, max:')
    print('min: %d' % min(data_int16))
    print('max: %d' % max(data_int16))


    # TODO - maybe this implicit int16 -> float conversion is wrong? maybe we need to have an intermediate Numpy-int16 array to make sure bytes are copied correctly (endianness, signed/unsigned, etc...)???
    #voltage_signal = np.fromiter(data_int16, dtype=float)
    tmp = np.fromiter(data_int16, dtype=np.int16)
    # TODO convert to float
    voltage_signal = tmp.astype(np.float64, casting='safe') # TODO may be able to reduce to float32
    voltage_signal = (voltage_signal * v_range.value / 65536) + v_offset.value
    return voltage_signal 





def print_scope_capabilities(dwf, hdwf):
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
    print('Scope Voltage MAX Range Info:')
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

    print('Scope Voltage MAX Offset Info:')
    print('min: %f' % min_voltage_offset.value) 
    print('max: %f' % max_voltage_offset.value)
    print('steps: %f' % steps_voltage_offset.value)


def print_scope_settings(dwf, hdwf):
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



### ctypes Helpers

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
