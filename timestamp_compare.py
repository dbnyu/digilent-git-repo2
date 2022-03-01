"""Compare timestamps from RRF file and Digilent.


    Doug Brantner
    3/1/2022
"""


import datetime
import os
import pandas as pd



data_dir = 'tofcamsynctest1'
ad2_times_file = '20220301-102012_timestamps.csv'   # direct output from timestamp_logger.py
rrf_times_file = 'royale_20220301_102007.rrf.csv'   # already parsed from RRF file with Matlab

# NOTE: AD2 times seem ok (units = seconds) as long as it's cast as int64
#       RRF times need to be integer-divided by 1,000,000 (to convert usec -> whole sec)
#           being careful to maintain datatype as int64

# TODO should main datatype be uint? or int64? (int64 seems to work so far)


def print_timestamp(t, s='', f=None):
    """Pretty-print a timestamp with default or optional format string.

        t = time to print (int64 seconds since unix epoch)
        s = optional description string
        f = optional format string for strftime (omit for default)
    """
    if f is None:
        f = "%Y-%m-%d_%H:%M:%S.%f"

    if s:
        s = s + ' ' # add space after

    print('%s%s' % (s, datetime.datetime.strftime(t, f)))



def print_start_end(t):
    """Print human readable datetimes for beginning & end of time array.

        NOTE: Times must be type=int64 
                    and
              in units of milliseconds (or Seconds???)

        t = array of timestamps as seconds

    """
    print(t.min())
    print(t.max())
    
    # TODO can this work with float datatypes??? losing fractions of seconds...

    print(type(t[0]))
    t0 = datetime.datetime.fromtimestamp(t.min())
    t1 = datetime.datetime.fromtimestamp(t.max())

    #print('Start: %s' % datetime.datetime.strftime(t0, "%Y-%m-%d_%H:%M:%S.%f"))
    #print('End  : %s' % datetime.datetime.strftime(t1, "%Y-%m-%d_%H:%M:%S.%f"))
    print_timestamp(t0, 'Start:')
    print_timestamp(t1, 'End  :')



ad2_times = pd.read_csv(os.path.join(data_dir, ad2_times_file), 
                        sep=',', 
                        header=None,
                        names=['trig_utc_sec', 'trig_ticks', 'ticks_per_sec'],
                        dtype=float,     # TODO is this ok? or overflow/keep as int?
                            # TODO need float to convert the milliseconds... but int64 seems preferred by datetime.
                        )

ad2_times['time'] = ad2_times.trig_utc_sec + ad2_times.trig_ticks/ad2_times.ticks_per_sec   # time in seconds.decimals
ad2_times['time_int'] = ad2_times['time'].astype('int64')
#print('full column cast to int:')
#print(type(ad2_times['time_int'][0]))


rrf_times = pd.read_csv(os.path.join(data_dir, rrf_times_file), 
                        #sep=',',
                        header=None,
                        names=['time'],
                        dtype='int64',
                        )
rrf_times['time_int'] = rrf_times['time'] // 1000000    # convert usec -> sec but keep as int64

# NOTE: from here on, the 'time_int' columns should be used
#   datatype: int64
#   units:    seconds

print('ad2_times:')
print(ad2_times['time'].head())
print(ad2_times['time'].shape)
#print_start_end((1000 * ad2_times['time']).astype(int))
#print_start_end((1000 * ad2_times['time']))
print_start_end((ad2_times['time_int']))

print()

print('rrf_times:')
print(rrf_times['time'].head())
print(rrf_times['time'].shape)
#print_start_end(1000000 * rrf_times['time'])
#print_start_end(rrf_times['time'] // 1000000)
print_start_end((rrf_times['time_int']))





# TODO generalize this:
# find the latest start time (whichever started 2nd)
# then find the nearest timestamp in the other file, ie. to sync the first frame

# assuming AD2 started after the RRF recording:

# subtract the start time to search for (of later AD2 file in this case)
# vectorwise from the full array of earlier start timestamps
# then find the min(abs()) of the differences to find the *closest* matching timestamp.
# UNITS MUST BE THE SAME!!!

# TODO something is wrong.. rounding to seconds... because of strftime????
# TODO need to keep fractinos of seconds!!!


searchtime = ad2_times['time_int'][0]
timediffs = rrf_times['time_int'] - searchtime
min_index = timediffs.abs().argmin()    # index into RRF array closest to AD2 start time

rrf_match_time = rrf_times['time_int'][min_index]

print_timestamp(datetime.datetime.fromtimestamp(searchtime),     'AD2 time to find:')
print_timestamp(datetime.datetime.fromtimestamp(rrf_match_time), 'RRF nearest time:')
difference = searchtime - rrf_match_time
print('Difference (sec): ', difference)
