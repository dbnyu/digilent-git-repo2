"""Plot respective channels from 2 CSV files against each other.

    Expects int16 files & converts to voltage automatically.

    Makes 2 plots: file1-ch1 and file2-ch1; and 
                   file1-ch2 and file2-ch2
"""



# TODO get correct voltage range/offset values

import ad2_tools as ad2
import matplotlib.pyplot as plt
import sys
#import argparse
import os


file1 = sys.argv[1]
file2 = sys.argv[2]
title = sys.argv[3]


LEGEND_LOC = 'upper right'  # best to fix this with large number of points


data1 = ad2.load_2ch_int16_csv(file1)
data2 = ad2.load_2ch_int16_csv(file2)

# these seem to be common values - may change if scope is manually recalibrated...
# TODO use correct values not defaults:
DEFAULT_CH1_RANGE  =  5.538410
DEFAULT_CH1_OFFSET =  0.000291
DEFAULT_CH2_RANGE  =  5.546847
DEFAULT_CH2_OFFSET = -0.000028


ad2.conv_volts_2ch_int16(data1, 
                         DEFAULT_CH1_RANGE,
                         DEFAULT_CH1_OFFSET,
                         DEFAULT_CH2_RANGE,
                         DEFAULT_CH2_OFFSET,
                         )

ad2.conv_volts_2ch_int16(data2, 
                         DEFAULT_CH1_RANGE,
                         DEFAULT_CH1_OFFSET,
                         DEFAULT_CH2_RANGE,
                         DEFAULT_CH2_OFFSET,
                         )




plt.plot(data1.Time, data1.ch1_volts, '.-', label='File1 Ch1 (V)')
plt.plot(data2.Time, data2.ch1_volts, '.-', label='File2 Ch1 (V)')
plt.xlabel('Time (sec - TR delays omitted!)')
plt.ylabel('Volts')
plt.title(title + ' (Ch1)')
plt.legend(loc=LEGEND_LOC)
plt.show()



plt.plot(data1.Time, data1.ch2_volts, '.-', label='File1 Ch2 (V)')
plt.plot(data2.Time, data2.ch2_volts, '.-', label='File2 Ch2 (V)')
plt.xlabel('Time (sec - TR delays omitted!)')
plt.ylabel('Volts')
plt.title(title + ' (Ch2)')
plt.legend(loc=LEGEND_LOC)
plt.show()
