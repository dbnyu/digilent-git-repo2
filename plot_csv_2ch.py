"""Plot a 2-channel raw int16 CSV file.
    (both channels on same plot)


"""


# TODO get correct voltage range/offset values

import ad2_tools as ad2
import matplotlib.pyplot as plt
import sys
#import argparse
import os


filepath = sys.argv[1]
#parser = argparse.ArgumentParser(description='Plot 2-channel int16 files.')
#parser.add_argument('filepath', metavar='f', type=str, help='file to plot')
#parser.add_argument('title', metavar='t', type=str, help='plot title')
#parser.add_argument('plot_ints', metavar='i', type=bool, help='plot raw int16 values')



data = ad2.load_2ch_int16_csv(filepath)

# TODO save voltage settings & load them here...

# these seem to be common values - may change if scope is manually recalibrated...
DEFAULT_CH1_RANGE  =  5.538410
DEFAULT_CH1_OFFSET =  0.000291
DEFAULT_CH2_RANGE  =  5.546847
DEFAULT_CH2_OFFSET = -0.000028

# TODO use correct values not defaults:
ad2.conv_volts_2ch_int16(data, 
                         DEFAULT_CH1_RANGE,
                         DEFAULT_CH1_OFFSET,
                         DEFAULT_CH2_RANGE,
                         DEFAULT_CH2_OFFSET,
                         )


#print(data.head())


plt.plot(data.Time, data.ch1_volts, '.-', label='Ch1 (V)')
plt.plot(data.Time, data.ch2_volts, '.-', label='Ch2 (V)')
plt.xlabel('Time (sec - TR delays omitted!)')
plt.ylabel('Volts')
plt.title(os.path.basename(filepath))
plt.show()




# M-Mode (1 channel at a time):
# TODO NOTE this needs the TR_len to be updated for each file...
ad2.plot_m_mode(ad2.reshape_to_M_mode(data.ch1_volts, 8000, 0), 
                title=os.path.basename(filepath) + ' Ch1',
                ignore_rows=1000
                )
                

ad2.plot_m_mode(ad2.reshape_to_M_mode(data.ch2_volts, 8000, 0), 
                title=os.path.basename(filepath) + ' Ch2',
                ignore_rows=1000
                )
