"""Import an Ultrasound CSV and reshape as M-Mode matrix.
    
    for data from custom1MHzWave_record.py etc. (may require some modification ie. for 2 channels, etc...)

    WIP, in process of moving these to ad2_tools.py library functions...

    Doug Brantner 11/19/21
"""


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os


#us_file_dir = 'C:\Users\db162\OneDrive - NYU Langone Health\Next Gen Sensors\ultrasound\Tests\20211111_wristband_intitial';

main_dir = r'C:\Users\db162\OneDrive - NYU Langone Health\Next Gen Sensors\ultrasound\Tests\20211117_patient_usmri'
ultrasound_dir = 'ultrasound_data'
metadata = pd.read_excel(os.path.join(main_dir, 'invivo20211117_metadata.xlsx'),
                         #dtype={'firstPeakIndex':int,  # TODO not working
                         #       'secondPeakIndex':int,
                         #       'weakExcitation':bool,
                         #       },
                         comment='#',
                         )


def reshape_to_M_mode(us_data, tr_len, firstpeak):
    """Reshape 1-D signal array to M-mode matrix.
        
        see original Matlab version

        us_data = Pandas dataframe, must contain 'Voltage' column as signal.

        Returns numpy 2-D array/matrix (TODO proper terminology here?)
    """

    #print('tr_len: ', tr_len)
    #print('firstpeak: ', firstpeak)

    tr_len = assert_int(tr_len)
    firstpeak = assert_int(firstpeak)

    new_len = us_data.Voltage.shape[0] - firstpeak + 1

    #print('tr_len: ',tr_len)
    #print('firstpeak: ', firstpeak)
    #print('new_len: ', new_len)
    
    n_periods = assert_int(np.floor(new_len // tr_len))

    last_index = firstpeak + n_periods*tr_len - 1
    #print('new shape: ', tr_len, n_periods)

    # note +1 on last_index because python end-indexes are not inclusive!
    return np.reshape(np.array(us_data.Voltage[firstpeak:last_index+1]), 
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


print(metadata)


file_index = 0  # index of file to open

data = pd.read_csv(os.path.join(main_dir, ultrasound_dir, metadata.Filename[file_index]),
                    names=['Index', 'Time', 'Voltage'],
                    dtype={'Index':int}
                   )

print(data.head())


# Confirm that first peak index is correct
plt.plot(data.Voltage[0:1000], label='Voltage')
firstpeak = metadata.firstPeakIndex[file_index] - 1;    # adjust 1-based index to 0-based
#plt.plot(data.iloc[firstpeak, 1], data.iloc[firstpeak, 3], '*', label='firstpeak')
plt.plot(data.Index[firstpeak], data.Voltage[firstpeak], '*', label='firstpeak')
plt.title('File %d Peak Confirm' % file_index)
plt.show()



M = reshape_to_M_mode(data, 400, firstpeak)




# display M-mode
# TODO extents to fill window?
# https://stackoverflow.com/questions/13384653/imshow-extent-and-aspect/13390798#13390798
plt.imshow(M, cmap='gray', aspect='auto')
plt.colorbar()
plt.show()
