"""Helper Functions for Digilent Analog Discovery 2.

    BASIC PARED DOWN VERSION TO AVOID UNNECESSARY IMPORTS.
    see ad2_tools.py for full version.

    This version is customized for timestamp_record.py

    Requires Waveforms and Waveforms SDK.
    Requires ctypes
    Requires Numpy

    The 'hdfw' object should be initialized & passed from the calling program.

    Doug Brantner 12/7/2021
"""


from ctypes import *
#import matplotlib.pyplot as plt
#import numpy as np
#import pandas as pd
import datetime
import sys

# contstants

NAN = float('nan')      # for initializing test values


# Scope Settings Class
# To get and store oscilloscope intput parameters

class ScopeParams():
    """Access and store AD2 oscilloscope settings.

        Takes care of all ctypes conversions; everything here
        is stored as regular Python types ie. 'float'
    """

    def __init__(self, dwf, hdwf):
        # hardware access constants:
        self.dwf = dwf
        self.hdwf = hdwf

        # scope parameters (to be populated at runtime):
        self.ch1_v_range = NAN
        self.ch2_v_range = NAN
        self.ch1_v_offset = NAN
        self.ch2_v_offset = NAN

        self.ch1_attenuation = NAN
        self.ch2_attenuation = NAN

        self.trigger_pos = NAN
        self.trigger_holdoff_time = NAN
        self.trigger_timeout = NAN


    def get_scope_params(self):
        """Get current settings from AD2 and set this object's member values.

           AD2 must be plugged in & scope must be ENABLED
           to get valid data.

           This handles ctypes conversions as well.
        """

        ch1_current_v_range = c_double(NAN)
        ch2_current_v_range = c_double(NAN)
        ch1_current_v_offset = c_double(NAN)
        ch2_current_v_offset = c_double(NAN)
    
        self.dwf.FDwfAnalogInChannelRangeGet(self.hdwf, c_int(0), byref(ch1_current_v_range))
        self.dwf.FDwfAnalogInChannelRangeGet(self.hdwf, c_int(1), byref(ch2_current_v_range))
        self.dwf.FDwfAnalogInChannelOffsetGet(self.hdwf, c_int(0), byref(ch1_current_v_offset))
        self.dwf.FDwfAnalogInChannelOffsetGet(self.hdwf, c_int(1), byref(ch2_current_v_offset))

    
        ch1_attenuation = c_double(NAN)
        ch2_attenuation = c_double(NAN)
        self.dwf.FDwfAnalogInChannelAttenuationGet(self.hdwf, c_int(0), byref(ch1_attenuation))
        self.dwf.FDwfAnalogInChannelAttenuationGet(self.hdwf, c_int(1), byref(ch2_attenuation))

        current_trigger_pos = c_double(NAN)
        self.dwf.FDwfAnalogInTriggerPositionGet(self.hdwf, byref(current_trigger_pos))

        trigger_holdoff_time = c_double(NAN)
        self.dwf.FDwfAnalogInTriggerHoldOffGet(self.hdwf, byref(trigger_holdoff_time))

        trigger_timeout = c_double(NAN)
        self.dwf.FDwfAnalogInTriggerAutoTimeoutGet(self.hdwf, byref(trigger_timeout))


        # ctypes to python type conversion:
        # TODO explicit float() casting?
        self.ch1_v_range  = ch1_current_v_range.value
        self.ch2_v_range  = ch2_current_v_range.value
        self.ch1_v_offset = ch1_current_v_offset.value
        self.ch2_v_offset = ch2_current_v_offset.value

        self.ch1_attenuation = ch1_attenuation.value
        self.ch2_attenuation = ch2_attenuation.value

        self.trigger_pos = current_trigger_pos.value
        self.trigger_holdoff_time = trigger_holdoff_time.value 
        self.trigger_timeout = trigger_timeout.value 

        # TODO print function

    def write_vconv_file(self, filepath):
        """Write voltage conversion settings to file.

            This includes *most* but not all of the Oscilloscope input settings;
            enough to properly convert raw int16 values to correct voltage values.

            filepath = full path including filename & extension (should be .csv)

            This writes a 2-line CSV file
                line 1 = headers
                line 2 = data
                sort of like a horizontal config file.
        """

        csv_headers = ','.join(['ch1_v_range',
                                'ch2_v_range',
                                'ch1_v_offset',
                                'ch2_v_offset',
                                'ch1_attenuation',
                                'ch2_attenuation',
                                'trigger_pos',
                                'trigger_holdoff_time',
                                'trigger_timeout',
                                ])

        csv_data = ','.join([ str(val) for val in [self.ch1_v_range,
                                                   self.ch2_v_range,
                                                   self.ch1_v_offset,
                                                   self.ch2_v_offset,
                                                   self.ch1_attenuation,
                                                   self.ch2_attenuation,
                                                   self.trigger_pos,
                                                   self.trigger_holdoff_time,
                                                   self.trigger_timeout,
                                                   ]])

        with open(filepath, 'w') as f:
            f.write(csv_headers)
            f.write('\n')
            f.write(csv_data)


# General Waveforms/DWF setup:

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





# scope setup & value conversion:



def get_volts_from_int16(dwf, hdwf, channel, data_int16, v_range=None, v_offset=None):
    """Convert raw oscilloscope 16-bit int data back to proper voltages.

        Wrapper for int16signal2voltage - this will poll the AD2 scope for 
        the correct range/offset values but THIS ONLY WORKS WHILE SCOPE IS ENABLED.
        This function will ONLY work correctly DURING the same acquisition.
            and is likely to be depreated soon... should be storing these values in metadata.

        # TODO could do this after acquisition but before closing scope; and then save
        # the int16 and double (volts) values at the same time...


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
    # TODO - if polling the scope dwf call for range/offset, may need to do it WHILE the scope is enabled
    #        otherwise the 'Get' calls don't work right (?)

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

    return int16signal2voltage(data_int16, v_range.value, v_offset.value)



def calc_trigger_pos_from_index(index_offset, dt, acq_time):
    """Return a time offset value for trigger position, for Waveforms SDK.

        index_offset = number of positions to offset the trigger time [int]
                ie. 10 = set the trigger to start on the 10th sample
                -----> 10 samples of pre-roll, then the trigger & actual acquisition

                set index = 0 for trigger to fall on the first sample
                            i.e. no pre-roll

        dt = time period for 1 sample (ie. 1/sample frequency) [seconds]
        acq_time = time duration of 1 full acquisition [seconds]

        Returns:
        trigger_position_time, the time value to shift the trigger from the
            center of the acquisition toward the beginning
            (ie. a positive offset will start the trigger earlier in the buffer)
            use this as input to FDwfAnalogInTriggerPositionSet()

        NOTE this is approximate since it's based on dt values so may be off by 1 or so...
    """
    # TODO can't take a ceiling of offset_time because it's probably microseconds << 1
    # but any way to nudge an off-by-one higher (ie. maximize the buffer offset toward +1 sample?)
    offset_time = index_offset * dt
    trigger_position_time = 0.5 * acq_time  # default trigger is middle of the buffer
    trigger_position_time -= offset_time

    # TODO bounds check? this probably should be >= 0
    return trigger_position_time 



# scope parameters access/printing: (see also class 

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

        NOTE - this only works while scope is enabled.

        For all channels:
            voltage range
            voltage offset

        See print_scope_capabilities for static variables.
    """
    # TODO this may be depredated by ScopeParams class...

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


### File Import/Export

### Custom CSV format:
# NOTE - there are a few different CSV formats floating around - need to unify...
#   - 1 channel vs. 2 channel signal
#   - double-type voltages vs. int16 raw ADC values




### Convert to M-Mode

def reshape_to_M_mode(us_data, tr_len, firstpeak):
    """Reshape 1-D signal array to M-mode matrix.

        us_data = 1D Numpy array of A-mode (voltage) signals
        tr_len  = number of samples (int) for 1 pulse/echo acquisition period
        firstpeak = index into us_data to use as first M-mode data point
                    e.g. the first peak of the excitation or sync pulse

                    Data before this is thrown away, and then as many integer
                    multiples of tr_len are taken, and any partial/trailing data
                    is also thrown away (so at most, 1 partial TR period at the
                    beginning and/or end will be lost).

                    For already-aligned data i.e. for fixed-length triggered 
                    acquisitions, firstpeak=0 should work to keep all data.
        
        See original Matlab version for more details.

        Returns numpy 2-D array/matrix (TODO proper terminology here?)
    """

    #print('tr_len: ', tr_len)
    #print('firstpeak: ', firstpeak)

    tr_len = assert_int(tr_len)
    firstpeak = assert_int(firstpeak)

    #new_len = us_data.Voltage.shape[0] - firstpeak + 1
    new_len = us_data.shape[0] - firstpeak + 1

    #print('tr_len: ',tr_len)
    #print('firstpeak: ', firstpeak)
    #print('new_len: ', new_len)
    
    n_periods = assert_int(np.floor(new_len // tr_len))

    last_index = firstpeak + n_periods*tr_len - 1
    #print('new shape: ', tr_len, n_periods)

    # note +1 on last_index because python end-indexes are not inclusive!
    #return np.reshape(np.array(us_data.Voltage[firstpeak:last_index+1]), 
    return np.reshape(np.array(us_data[firstpeak:last_index+1]), 
                      (tr_len, n_periods),
                      order='F')    # note Fortran index order


def assert_int(i):
    """Safely cast i to int datatype, throwing error if the value
        is non-integer (ie. avoid rounding 4.00001 to 4)

        Only use this if the input is expected to be integer-valued,
        but not necessarily int-type.
    """
    tmp = i
    i = int(i)
    if i != tmp:
        raise ValueError('Input i=%f has non-integer value', tmp)
    return i



### Plotting
# - see full ad2_tools.py






# General Utilities

def get_timestamp():
    """Return pre-formatted timestamp."""
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
