"""Plot a 2-channel raw int16 CSV file.
    (both channels on same plot)


"""


# TODO get correct voltage range/offset values

import ad2_tools as ad2
import matplotlib.pyplot as plt
import pandas as pd
import sys
#import argparse
import os


C_WATER = 1482.3    # m/s
MEDIUM = 'water'

#C_AIR = 343.0       # m/s
#MEDIUM = 'air'



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


file_desc = filepath.split('_')[1]

# try default voltage conversion filename:
vconv_file = filepath.rsplit('_', 1)[0] + '_vconv.csv'
try: 
    vconv_data = pd.read_csv(vconv_file)
    #print(vconv_data.head())

    print('Using voltage conv. params from file:')
    print('ch1_v_range: %s' % str(vconv_data.ch1_v_range[0]))
    print('ch1_v_offset: %s' % str(vconv_data.ch1_v_offset[0]))
    print('ch2_v_range: %s' % str(vconv_data.ch2_v_range[0]))
    print('ch2_v_offset: %s' % str(vconv_data.ch2_v_offset[0]))

    ad2.conv_volts_2ch_int16(data, 
                             vconv_data.ch1_v_range[0],
                             vconv_data.ch1_v_offset[0],
                             vconv_data.ch2_v_range[0],
                             vconv_data.ch2_v_offset[0]
                             )

except FileNotFoundError as e:
    # use default values if file doesn't exist
    print('File not found: %s' % vconv_file)
    print('Using default voltage conversion parameters.')
    print('\tNOTE: these may be approximate or wrong!')

    vconv_data = None

    # TODO use correct values not defaults:
    ad2.conv_volts_2ch_int16(data, 
                             DEFAULT_CH1_RANGE,
                             DEFAULT_CH1_OFFSET,
                             DEFAULT_CH2_RANGE,
                             DEFAULT_CH2_OFFSET,
                             )


#print(data.head())


distscale = 1000 * data.Time * C_WATER  # convert to mm





plt.plot(data.Time, data.ch1_volts, '.-', label='Ch1 (V)')
plt.plot(data.Time, data.ch2_volts, '.-', label='Ch2 (V)')
plt.xlabel('Time (sec - TR delays omitted!)')
plt.ylabel('Volts')
#plt.title(os.path.basename(filepath))
plt.title(file_desc)
plt.show()




# plot 2 channels as separate subplots
# distance as X axis; linked zoom on x axis:
# https://stackoverflow.com/questions/4200586/matplotlib-pyplot-how-to-zoom-subplots-together
ax_ch1 = plt.subplot(2, 1, 1)
ax_ch1.plot(distscale, data.ch1_volts, '.-', label='Ch. 1 (V)')

#plt.title('%s @ SR=%.2e Hz (TR=%.2e s)' % (file_desc, INPUT_SAMPLE_RATE, INPUT_SINGLE_ACQUISITION_TIME))
plt.title('%s' % file_desc)

ax_ch2 = plt.subplot(2, 1, 2, sharex=ax_ch1)
ax_ch2.plot(distscale, data.ch2_volts, '.-', color='tab:orange', label='Ch. 2 (V)')

ax_ch1.set_xlabel('Distance [mm] (take diffs!)')
ax_ch2.set_xlabel('Distance [mm] (take diffs!)')
ax_ch1.set_ylabel('Ch. 1 Volts')    
ax_ch2.set_ylabel('Ch. 2 Volts')    
#plt.title('Signals Shown Separately')
plt.show()





# TODO - come back to this!
# M-Mode (1 channel at a time):
# TODO NOTE this needs the TR_len to be updated for each file...
#ad2.plot_m_mode(ad2.reshape_to_M_mode(data.ch1_volts, 8000, 0), 
#                title=file_desc + ' Ch1',
#                #title=os.path.basename(filepath) + ' Ch1',
#                ignore_rows=1000
#                )
#                
#
#ad2.plot_m_mode(ad2.reshape_to_M_mode(data.ch2_volts, 8000, 0), 
#                title=file_desc + ' Ch2',
#                #title=os.path.basename(filepath) + ' Ch2',
#                ignore_rows=1000
#                )
