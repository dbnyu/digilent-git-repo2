"""Helper Functions for Digilent Analog Discovery 2.

    Requires Waveforms and Waveforms SDK.
    Requires ctypes
    Requires Numpy

    The 'hdfw' object should be initialized & passed from the calling program.

    Doug Brantner 12/7/2021
"""


from ctypes import *
import matplotlib.pyplot as plt
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

    #if len(err_str) > 0:    # TODO make this work for ctypes converted string...
    #if err_str[0] != b'\0':
    #if err_str[0] != 0x00:
    if err_str != "b''":        # TODO hack, maybe clamp down on the b-string weirdness in get_error... but nice to see when it is empty (when verbose is wanted)
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

    print('Numpy int16 min/max:')
    print('min: %d' % np.min(data_int16))
    print('max: %d' % np.max(data_int16))

    voltage_signal = tmp.astype(np.float64, casting='safe') # TODO may be able to reduce to float32

    print('Numpy float min/max:')
    print('min: %d' % np.min(voltage_signal))
    print('max: %d' % np.max(voltage_signal))

    voltage_signal = (voltage_signal * v_range.value / 65536) + v_offset.value
    return voltage_signal 





def print_scope_capabilities(dwf, hdwf):
    """Print static info on the scope (ie. min/max possible voltage range)
        Things that are fixed in the hardware and not changeable at runtime.

        see also print_scope_settings() for querying changeable settings.
    """

    print("################################")
    print("####### AD2 Scope Limits #######")


    # voltage input range
    min_voltage_range = c_double(NAN)
    max_voltage_range = c_double(NAN)
    steps_voltage_range = c_double(NAN)
    
    dwf.FDwfAnalogInChannelRangeInfo(hdwf,
                                     byref(min_voltage_range),
                                     byref(max_voltage_range),
                                     byref(steps_voltage_range),
                                     )
    print('Voltage Range Info:')
    print('min: %f (V)' % min_voltage_range.value) 
    print('max: %f (V)' % max_voltage_range.value)
    print('steps: %f' % steps_voltage_range.value)
    
    print()
    
    # voltage input offset
    min_voltage_offset = c_double(NAN)
    max_voltage_offset = c_double(NAN)
    steps_voltage_offset = c_double(NAN)
    
    dwf.FDwfAnalogInChannelOffsetInfo(hdwf, 
                                      byref(min_voltage_offset),
                                      byref(max_voltage_offset),
                                      byref(steps_voltage_offset)
                                      )

    print('Voltage Offset Info:')
    print('min: %f (V)' % min_voltage_offset.value) 
    print('max: %f (V)' % max_voltage_offset.value)
    print('steps: %f' % steps_voltage_offset.value)

    print()
    
    # trigger position (in time)
    min_trigger_pos = c_double(NAN)
    max_trigger_pos = c_double(NAN)
    steps_trigger_pos = c_double(NAN)

    dwf.FDwfAnalogInTriggerPositionInfo(hdwf, 
                                        byref(min_trigger_pos),
                                        byref(max_trigger_pos),
                                        byref(steps_trigger_pos)
                                        )
    print('min trigger position: %f (sec)' % min_trigger_pos.value)
    print('max trigger position: %f (sec)' % max_trigger_pos.value)
    print('steps: %f' % steps_trigger_pos.value)

    print()

    # Trigger Holdoff
    min_holdoff = c_double(NAN)
    max_holdoff = c_double(NAN)
    steps_holdoff = c_double(NAN)

    dwf.FDwfAnalogInTriggerHoldOffInfo(hdwf,
                                       byref(min_holdoff),
                                       byref(max_holdoff),
                                       byref(steps_holdoff)
                                       )
    print('min trigger holdoff: %f (sec)' % min_holdoff.value)
    print('max trigger holdoff: %f (sec)' % max_holdoff.value)
    print('steps: %f' % steps_holdoff.value)

    print()

    # Trigger Timeout
    min_timeout = c_double(NAN)
    max_timeout = c_double(NAN)
    steps_timeout = c_double(NAN)


    dwf.FDwfAnalogInTriggerAutoTimeoutInfo(hdwf,
                                           byref(min_timeout),
                                           byref(max_timeout),
                                           byref(steps_timeout)
                                           )
    print('min trigger timeout: %f (sec)' % min_timeout.value)
    print('max trigger timeout: %f (sec)' % max_timeout.value)
    print('steps: %f' % steps_timeout.value)


    print("####### End Scope Limits #######")
    print("################################")

    # TODO what's the difference between 'get' and 'status' methods? eg. with TriggerPosition???




def print_scope_settings(dwf, hdwf):
    """Access and print basic scope settings (User-changeable ones):

        For all channels:
            voltage range
            voltage offset

        See print_scope_capabilities for static variables.
    """

    # TODO is this working? getting all zeros for range/offset (range should be 5-25)

    ch1_current_v_range = c_double(NAN)
    ch2_current_v_range = c_double(NAN)
    
    ch1_current_v_offset = c_double(NAN)
    ch2_current_v_offset = c_double(NAN)
    
    
    dwf.FDwfAnalogInChannelRangeGet(hdwf, c_int(0), byref(ch1_current_v_range))
    dwf.FDwfAnalogInChannelRangeGet(hdwf, c_int(1), byref(ch2_current_v_range))
    
    dwf.FDwfAnalogInChannelOffsetGet(hdwf, c_int(0), byref(ch1_current_v_offset))
    dwf.FDwfAnalogInChannelOffsetGet(hdwf, c_int(1), byref(ch2_current_v_offset))
    print('Ch.1 v range, offset: %f, %f' % (ch1_current_v_range.value, ch1_current_v_offset.value))
    print('Ch.2 v range, offset: %f, %f' % (ch2_current_v_range.value, ch2_current_v_offset.value))

    
    ch1_attenuation = c_double(NAN)
    ch2_attenuation = c_double(NAN)

    dwf.FDwfAnalogInChannelAttenuationGet(hdwf, c_int(0), byref(ch1_attenuation))
    dwf.FDwfAnalogInChannelAttenuationGet(hdwf, c_int(1), byref(ch2_attenuation))
    print('Ch.1, Ch.2 Attenuation: %f, %f' % (ch1_attenuation.value, ch2_attenuation.value))

    current_trigger_pos = c_double(NAN)
    dwf.FDwfAnalogInTriggerPositionGet(hdwf, byref(current_trigger_pos))
    print('Trigger Position    : %f (sec)' % current_trigger_pos.value)

    trigger_holdoff_time = c_double(NAN)
    dwf.FDwfAnalogInTriggerHoldOffGet(hdwf, byref(trigger_holdoff_time))
    print('Trigger Holdoff Time: %f (sec)' % trigger_holdoff_time.value)

    trigger_timeout = c_double(NAN)
    dwf.FDwfAnalogInTriggerAutoTimeoutGet(hdwf, byref(trigger_timeout))
    print('Trigger Timeout     : %f (sec)' % trigger_timeout.value) 


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





### Plotting

def bland_altman(y1, y2):
    """Make a Bland-Altman Plot to compare 2 similar signals.

        y1, y2 = 2 vectors, measurements of the same signal to compare
    """
    # TODO possible to pass kwargs to plot()?

    # TODO return a handle to the plot, which can be used to set the title/xlabel/etc. later?
    

    mean = 0.5 * (y1 + y2);
    diff = y1 - y2;

    plt.plot(mean, diff, '.')
    plt.title('Bland Altman')
    plt.xlabel('Mean')
    plt.ylabel('Difference')

    mean_of_diff = np.mean(diff)
    std_of_diff = np.std(diff)

    print('Mean of difference: %f' % mean_of_diff)
    print('Std. of difference: %f' % std_of_diff)

    plt.axhline(mean_of_diff, color='k', linestyle='-', label='mean of diff') 
    plt.axhline(std_of_diff,  color='k', linestyle='--', label='+stddev')
    plt.axhline(-std_of_diff, color='k', linestyle='--', label='-stddev')

    plt.show()
