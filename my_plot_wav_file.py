"""Import a WAV file and plot it.

    Usage:

    python plot_wav_file.py <filename> [frequency]
        filename = name or path to WAV file, required
        frequency = frequency (in Hz) of original signal, if known
                    optional - used for filtering peaks
                    anyth string parseable by float() is acceptable e.g. 1e6 for 1 MHz.

    Based on:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.wavfile.read.html
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import find_peaks
from scipy.fft import fft, fftfreq
import sys

plot_waveform = True    # crashes with too many points

try:
    filepath = sys.argv[1]
except IndexError:
    print('Filename required. Quitting.')
    sys.exit(1)

try:
    # this is optional:
    wavefreq = float(sys.argv[2])  # assuming clean sine wave, the frequency of the original signal (for filtering peaks)
    filter_peaks = True
except IndexError:
    wavefreq = None
    filter_peaks = False

try:
    samplerate, wavedata = wavfile.read(filepath)
except FileNotFoundError:
    print("Invalid filename. Quitting.")
    sys.exit(1)

print("shape:")
print(wavedata.shape)

record_length = wavedata.shape[0] / samplerate # recorded time in seconds

try:
    n_channels = wavedata.shape[1]
except IndexError:
    # assuming if shape = (80000, ) with no 2nd entry, then it's a "mono" file TODO check this???
    n_channels = 1

print('Number of channels:\t%d' % n_channels)

print('Sample Rate       :\t%d (Hz)' % samplerate)
print('Length of time    :\t%f (sec)' % record_length)
print('Number of Samples :\t%d' % wavedata.shape[0])
sample_dt = 1. / samplerate
print('Sample dt         :\t%f (sec)' % sample_dt)


print('\n\n')

print('wavedata type:\t%s' % type(wavedata))
print('wavedata type:\t%s' % type(wavedata[0]))
print('Min Amplitude:\t%d' % np.min(wavedata))
print('Max Amplitude:\t%d' % np.max(wavedata))

print('\n\n')
peak_prominence_pct = 0.9
peak_prominence = peak_prominence_pct * float(np.max(wavedata))

print('Prominence threshold percent:\t%f', peak_prominence_pct) 
print('Prominence threshold value  :\t%f', peak_prominence) 


# find peaks (assuming clean sine waves):
# TODO assuming single vector:
peak_indexes, peak_props = find_peaks(wavedata, prominence=peak_prominence)


print('\n\n')
peak_count = peak_indexes.shape[0]
print('Peak count:\t%d' % peak_count)
peak_freq = float(peak_count) / record_length   # rough approximation of signal frequency 
print('Rough freq:\t%f\t(#peaks/record length)' % peak_freq)


# zero crossings:
print('\n\n')
#zero_indexes = np.nonzero(wavedata == 0)[0]    # TODO naive zero finder, assuming ints that are exactly equal to zero (bad!)
#zero_indexes = np.nonzero(abs(wavedata) <= 100 )[0]    # for the 80Hz example, this shows min(abs) values ~100 - no exact zeros, and closely spaced near-doubles (see saved figure)

# TODO: try taking absolute value then finding minimums: zeros = minpeaks(abs(waveform)), or peaks(-1 * abs(waveform))
zero_indexes, zero_props = find_peaks(-1 * np.abs(wavedata))

print(zero_indexes)
print('Zero count:\t%d' % zero_indexes.shape[0])

# TODO START HERE:
# TODO - need better filtering of peaks and/or zeros
# TODO - lots of nearby duplicates -> filtering?
# TODO - how to analyze "cleanness" of wave over time? cross correlation? FFT w/ sliding window???
# TODO - correlation with time-aligned idealized duplicate (eg. generate analytic sine function w/ same frequency & amplitude, time align, then do correlation against that???)



# plotting
time = np.linspace(0., record_length, wavedata.shape[0]) # TODO this assumes properly time samples...

if plot_waveform:
    #plt.plot(time, -1*np.abs(wavedata), '.-', label='Mono Channel')

    #plt.plot(time, wavedata, '.-', label='Mono Channel')

    plt.plot(time, wavedata, '.-', label='Mono Channel')
    #plt.plot(time[peak_indexes], wavedata[peak_indexes], 'o', label='Peaks')
    #plt.plot(time[zero_indexes], wavedata[zero_indexes], '*', label='Zeros')
    
    plt.xlim([0, 200e-6])
    
    # TODO handle mono vs multiple channel indexing:
    #plt.plot(time, wavedata[:, 0], label='Left Channel')
    #if n_channels > 1:
    #    plt.plot(time, wavedata[:, 1], label='Right Channel')
    #plt.legend()
    plt.title('Waveform')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude') # TODO what is the standard scale for a WAV file? Do we need to store oscilloscope settings (voltage/div eg.) in metadata/filename?
    plt.show()




# FFT Plot:
# TODO basic version from here: https://docs.scipy.org/doc/scipy/reference/tutorial/fft.html
# TODO maybe the windowed version would be more accurate?
wave_fft = fft(wavedata)
N = wavedata.shape[0]
fft_freqs = fftfreq(N, sample_dt)[:N//2]    # TODO figure out this indexing/truncation

#figure()
plt.plot(fft_freqs, 2./N *  np.abs(wave_fft[0:N//2]))
plt.grid()
plt.title('FFT (basic)')
plt.xlabel('Frequency (Hz)')
plt.show()

# TODO semilog plot?
# TODO find peak frequencies?
