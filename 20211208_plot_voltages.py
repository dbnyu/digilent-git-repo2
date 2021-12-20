"""Data analysis from silicone phantom experiments 12/08/2021.

    Recorded single pulse/acquisition with different setups
    with (water?) filled silicone phantom; no other objects.

    Used 10x sine wave packet and single rectangular pulse.

    TODO - 1usec duration rectangular pulse may be wrong- it might 
            need to be 0.5usec == 1/2 period of transducer center frequency...
            DOUBLE CHECK THIS!
"""
# NOTE - pulses are likely truncated at 2.7 V due to 5V range setting, which is intentional in order to capture the low-voltage echos better.


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import ad2_tools as ad2



## NOTE - to convert windows formatted path in cygwin terminal (ie. to be able to ls files):
#  ls "$(cygpath -u "C:\Users\db162\OneDrive - NYU Langone Health\Next Gen Sensors\ultrasound\Tests\20211208_phantomTests")"
# note double quoting because of spaces in dir name

# Result of:
# $ ls  -1tr "$(cygpath -u "C:\Users\db162\OneDrive - NYU Langone Health\Next Gen Sensors\ultrasound\Tests\20211208_phantomTests")"
# (list -1 file per line, sorted by time -t, reverse order -r)
#
# ad2_tools.py
# inUSgel_lgBUF_4milSample_lessarr_20211208-18h23m37s.csv
# inUSgel_lgBUF_4milSample_8ksample_1acq_20211208-18h37m31s.csv
# inUSgel_lgBUF_4milSample_8ksample_1acq_both5_20211208_18h41m00s.csv
# inUSgel_lgBUF_4milSample_8ksample_1acq_both5_20211208_18h43m42s.csv
# inUSgel_lgBUF_4milSample_8ksample_1acq_floating_20211208_18h50m27s.csv
# inUSgel_lgBUF_4milSample_8ksample_1acq_ySrR_20211208_18h56m19s.csv
# inUSgel_lgBUF_4milSample_lessarr_20211208-18h57m11s_flags.txt
# inUSgel_lgBUF_4milSample_lessarr_20211208-18h57m11s_available.txt
# inUSgel_lgBUF_4milSample_lessarr_20211208-18h57m11s.csv
# inUSgel_lgBUF_4milSample_8ksample_1acq_ySrR_sineDrive20211208_19h08m24s.csv
# inUSgel_lgBUF_4milSample_8ksample_1acq_ySrR_sineDrive20211208_19h08m24s_meta.txt
# inUSgel_lgBUF_4milSample_8ksample_1acq_ySrR_sineDrivelongerwaitbetween_20211208_19h17m26s.csv
# inUSgel_lgBUF_4milSample_8ksample_1acq_ySrR_sineDrivelongerwaitbetween_20211208_19h17m26s_meta.txt
# inUSgel_lgBUF_4milSample_8ksample_1acq_ySbR_sineDrivelongerwaitbetween_20211208_19h22m10s.csv
# inUSgel_lgBUF_4milSample_8ksample_1acq_ySbR_sineDrivelongerwaitbetween_20211208_19h22m10s_meta.txt
# inUSgel_lgBUF_4milSample_8ksample_1acq_ySbR_recPulse_20211208_19h25m45s.csv
# inUSgel_lgBUF_4milSample_8ksample_1acq_ySbR_recPulse_20211208_19h25m45s_meta.txt
# my_custom_trigger_16bit_2ch_phantom.py
# inUSgel_lgBUF_4milSample_8ksample_1acq_ySrR_recPulse_20211208_19h30m54s.csv
# inUSgel_lgBUF_4milSample_8ksample_1acq_ySrR_recPulse_20211208_19h30m54s.txt
# plot_ultrasoundbottle.m
# 20211208_testonbottle_summary.pptx


file_dir = r'C:\Users\db162\OneDrive - NYU Langone Health\Next Gen Sensors\ultrasound\Tests\20211208_phantomTests'

# phantom silicone sleeve with water (?)
# Yellow-Red = 90 degrees opposed transducers
# Yellow-Blue = 180 degrees opposed transducers

# 10x sine pulse wave packet pings:
sine_yr_file = 'inUSgel_lgBUF_4milSample_8ksample_1acq_ySrR_sineDrivelongerwaitbetween_20211208_19h17m26s.csv' # 90 degrees opposed, 10x sine wave packet pulse
SINE_YR_V_CH1_RANGE = 5.538410  # from meta file
SINE_YR_V_CH1_OFFSET = 0.000291
SINE_YR_V_CH2_RANGE = 5.546847
SINE_YR_V_CH2_OFFSET = -0.000028

sine_yb_file = 'inUSgel_lgBUF_4milSample_8ksample_1acq_ySbR_sineDrivelongerwaitbetween_20211208_19h22m10s.csv' # 180 degrees opposed, 10x sine wave packet pulse
SINE_YB_V_CH1_RANGE  =  5.538410
SINE_YB_V_CH1_OFFSET =  0.000291
SINE_YB_V_CH2_RANGE  =  5.546847
SINE_YB_V_CH2_OFFSET = -0.000028


# single rectangle pulse; 180 degrees opposed (yellow-blue)
rect_yb_file = 'inUSgel_lgBUF_4milSample_8ksample_1acq_ySbR_recPulse_20211208_19h25m45s.csv'
RECT_YB_V_CH1_RANGE  =  5.538410
RECT_YB_V_CH1_OFFSET =  0.000291
RECT_YB_V_CH2_RANGE  =  5.546847
RECT_YB_V_CH2_OFFSET = -0.000028

# single rectangle pulse; 90 degrees opposed (yellow-red)
rect_yr_file = 'inUSgel_lgBUF_4milSample_8ksample_1acq_ySrR_recPulse_20211208_19h30m54s.csv'
RECT_YR_V_CH1_RANGE  =  5.538410
RECT_YR_V_CH1_OFFSET =  0.000291
RECT_YR_V_CH2_RANGE  =  5.546847
RECT_YR_V_CH2_OFFSET = -0.000028




#def load_2ch_int16_csv(filepath):
#    """Load a 2-channel int16 CSV file."""
#
#    data = pd.read_csv(filepath,
#                       names=['Index', 'Time', 'ch1_int16', 'ch2_int16'],
#                       dtype={'Index':int}
#                       # TODO force int16 type, or just allow doubles?
#                       )
#    return data

C_AIR = 343.0;
C_WATER = 1482.3; # from https://itis.swiss/virtual-population/tissue-properties/database/acoustic-properties/speed-of-sound/
C_TISSUE = 1540;

def sec2dist(t, c):
    """Convert time to distance.

        t = time array (seconds)
        c = speed of sound (meters/second)

        Returns an array of distances in meters.
    """
    return c * t;   # distance = rate * time




data_90_sine10x =  ad2.load_2ch_int16_csv(os.path.join(file_dir, sine_yr_file))
data_180_sine10x = ad2.load_2ch_int16_csv(os.path.join(file_dir, sine_yb_file))

data_90_sine10x['ch1_volts'] = ad2.get_volts_from_int16(None, None, -1, 
                                                       data_90_sine10x.ch1_int16, 
                                                       v_range=SINE_YR_V_CH1_RANGE, 
                                                       v_offset=SINE_YR_V_CH1_OFFSET
                                                       )
data_90_sine10x['ch2_volts'] = ad2.get_volts_from_int16(None, None, -1, 
                                                       data_90_sine10x.ch2_int16, 
                                                       v_range=SINE_YR_V_CH2_RANGE, 
                                                       v_offset=SINE_YR_V_CH2_OFFSET,
                                                       )
data_180_sine10x['ch1_volts'] = ad2.get_volts_from_int16(None, None, -1, 
                                                       data_180_sine10x.ch1_int16, 
                                                       v_range=SINE_YB_V_CH1_RANGE, 
                                                       v_offset=SINE_YB_V_CH1_OFFSET
                                                       )
data_180_sine10x['ch2_volts'] = ad2.get_volts_from_int16(None, None, -1, 
                                                       data_180_sine10x.ch2_int16, 
                                                       v_range=SINE_YB_V_CH2_RANGE, 
                                                       v_offset=SINE_YB_V_CH2_OFFSET,
                                                       )


# TODO doing this fast... cehck for var names/copypasta errors/transpositions...

data_90_rectpulse =  ad2.load_2ch_int16_csv(os.path.join(file_dir, rect_yr_file))
data_180_rectpulse = ad2.load_2ch_int16_csv(os.path.join(file_dir, rect_yb_file))

data_90_rectpulse['ch1_volts'] = ad2.get_volts_from_int16(None, None, -1, 
                                                       data_90_rectpulse.ch1_int16, 
                                                       v_range= RECT_YR_V_CH1_RANGE, 
                                                       v_offset=RECT_YR_V_CH1_OFFSET
                                                       )
data_90_rectpulse['ch2_volts'] = ad2.get_volts_from_int16(None, None, -1, 
                                                       data_90_rectpulse.ch2_int16, 
                                                       v_range= RECT_YR_V_CH2_RANGE, 
                                                       v_offset=RECT_YR_V_CH2_OFFSET
                                                       )

data_180_rectpulse['ch1_volts'] = ad2.get_volts_from_int16(None, None, -1, 
                                                       data_180_rectpulse.ch1_int16, 
                                                       v_range= RECT_YB_V_CH1_RANGE, 
                                                       v_offset=RECT_YB_V_CH1_OFFSET
                                                       )
data_180_rectpulse['ch2_volts'] = ad2.get_volts_from_int16(None, None, -1, 
                                                       data_180_rectpulse.ch2_int16, 
                                                       v_range= RECT_YB_V_CH2_RANGE, 
                                                       v_offset=RECT_YB_V_CH2_OFFSET
                                                       )


print(data_90_sine10x.head())



# sine wave, ch1/ch2 90 degrees opposed
plt.plot(data_90_sine10x.Time, data_90_sine10x.ch1_volts, '.-', label='Sine10x Ch1')
plt.plot(data_90_sine10x.Time, data_90_sine10x.ch2_volts, '.-', label='Sine10x Ch2')
plt.title('Sine10x Pulse; 90-deg opposed (yellow-red)')
plt.xlabel('Seconds (single acquisition)')
plt.ylabel('Voltage')
plt.legend()
plt.show()

# rect pulse test 1, 90 deg. opposed
plt.plot(data_90_rectpulse.Time, data_90_rectpulse.ch1_volts, '.-', label='Rect1x Ch1')
plt.plot(data_90_rectpulse.Time, data_90_rectpulse.ch2_volts, '.-', label='Rect1x Ch2')
plt.title('Rectangular Pulse; 90-deg opposed (yellow-red)')
plt.xlabel('Seconds (single acquisition)')
plt.ylabel('Voltage')
plt.legend()
plt.show()



# plot rx-only compare different sensor angular arrangements (sine wave 10x pulse)
plt.plot(data_90_sine10x.Time,  data_90_sine10x.ch2_volts,  '.-', label='Sine10x 90deg Ch2')
plt.plot(data_180_sine10x.Time, data_180_sine10x.ch2_volts, '.-', label='Sine10x 180deg Ch2')
plt.title('90deg vs. 180deg opposed; sine10x pulse; Rx channel only')
plt.xlabel('Seconds (single acquisition)')
plt.ylabel('Voltage')
plt.legend()
plt.show()


# plot rx-only for rectangular pulse/different angles:
plt.plot(data_90_rectpulse.Time,  data_90_rectpulse.ch2_volts,  '.-', label='Rect1x 90deg Ch2')
plt.plot(data_180_rectpulse.Time, data_180_rectpulse.ch2_volts, '.-', label='Rect1x 180deg Ch2')
plt.title('90deg vs. 180deg opposed; Rectangle 1x pulse; Rx channel only')
plt.xlabel('Seconds (single acquisition)')
plt.ylabel('Voltage')
plt.legend()
plt.show()


# compare same channel/angle with different pings
plt.plot(data_90_sine10x.Time,    data_90_sine10x.ch1_volts,    '.-', label='Sine10x 90deg Ch1')
plt.plot(data_90_rectpulse.Time,  data_90_rectpulse.ch1_volts,  '.-', label='Rect1x 90deg Ch1')
plt.title('90-deg, different impulse, Direct Tx Channel only')
plt.xlabel('Seconds (single acquisition)')
plt.ylabel('Voltage')
plt.legend()
plt.show()


# compare same channel/angle with different pings
plt.plot(data_180_sine10x.Time,    data_180_sine10x.ch1_volts,    '.-', label='Sine10x 180deg Ch1')
plt.plot(data_180_rectpulse.Time,  data_180_rectpulse.ch1_volts,  '.-', label='Rect1x 180deg Ch1')
plt.title('180-deg, different impulse, Direct Tx Channel only')
plt.xlabel('Seconds (single acquisition)')
plt.ylabel('Voltage')
plt.legend()
plt.show()

#plt.plot(data_90_sine10x.Time,  data_90_sine10x.ch2_volts,  '.-', label='Sine10x 90deg Ch2')
