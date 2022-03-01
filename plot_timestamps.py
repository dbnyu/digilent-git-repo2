"""Plot dt values from a timestamp file recorded with timestamp_logger.py

    USAGE:
    python plot_timestamps.py <path to CSV file>

    Doug Brantner 2/28/2022
"""

# TODO differentiate ASCII file vs. binary file



import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import datetime


# TODO look into pandas automatic handling of datetimes...

filepath = sys.argv[1]


if not os.path.isfile(filepath):
    print('Error: File not found.')
    sys.exit(1)


# Read ASCII comma-separated/newline data:
data = pd.read_csv(filepath, 
                   sep=',', 
                   header=None,
                   names=['trig_utc_sec', 'trig_ticks', 'ticks_per_sec'],
                   dtype=float,     # TODO is this ok? or overflow/keep as int?
                   )


data['time'] = data.trig_utc_sec + data.trig_ticks/data.ticks_per_sec   # time in seconds.decimals

# zero the seconds (default is seconds since Unix Epoch)
#data.trig_utc_sec -= data.trig_utc_sec[0]
# NOTE - not needed, only looking at dt values
#data['dt_sec_only'] = data.trig_utc_sec.diff()

data['dt'] = data['time'].diff()


# get file timestamp from filename:
filename = os.path.basename(filepath)
print(type(filename))
print(filename)
filename = filename.split('.', 1)[0]
#filetimestamp = filename.split('_', 1)[0]
print(filename)
filetimestamp = filename.split('_', 1)[0]

print(filetimestamp)
filecreationtime = datetime.datetime.strptime(filetimestamp, "%Y%m%d-%H%M%S")
print('File Creation Time:')
print(filecreationtime.strftime("%Y-%m-%d %H:%M:%S.%f")) # TODO milliseconds



# find datetime of first timestamp (ie. delay between recording start/file creation and first actual trigger):
t0 = datetime.datetime.fromtimestamp(data['time'][0])   # TODO local/iso/zulu dates... time zone???

print('First Trigger:')
print(t0.strftime("%Y-%m-%d %H:%M:%S.%f")) # TODO milliseconds



delay1 = t0 - filecreationtime
print('Delay from file start to 1st trigger (sec):')
print(delay1.total_seconds())


#print('Avg. dt (sec only):')
##print(data['dt_sec_only'].mean())
#
#plt.plot(data.dt_sec_only, '.-')
#plt.title('dt (seconds only)')
#plt.xlabel('Timestamp Index')
#plt.ylabel('dt (seconds)')
#plt.show()

print()
print('Avg. dt:')
print(data['dt'].mean())


plt.plot(data['dt'], '.-')
plt.title('dt')
plt.xlabel('Timestamp Index')
plt.ylabel('dt (seconds)')
plt.show()
