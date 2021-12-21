function M = reshape_to_M_mode(voltage, tr_length, firstpeak)
%function M = reshape_to_M_mode(us_table, tr_length, firstpeak)
% Reshape a raw oscilloscope A-mode repeated pulse-echo signal to M-mode matrix
%
%	TODO - update all calling functions to new input
%	NEW INPUT:
%	voltage = vector of raw voltage samples (or raw int 16; scaling is arbitrary)
%				ie. all A-mode pulse/echo repeated signals as a single 1D array.
%				update - not a matlab table anymore, just a regular array/vector.
%
%	NOTE: DEPRECATED INPUT:
%	us_table = ultrasound CSV read in as a table object
%				(see load_ultrasound_csv.m)
%				'Voltage' column is required.
%
%	tr_length = length (in samples/indexes) of a single TR period
%				(aka. ultrasound pulse-echo period)
%				this becomes the height of the M-mode matrix
%
%	firstpeak = index of first excitation peak, to align signals
%				data before this is thrown away
%				and data after last complete TR period is also ignored.
%				(so you lose the first & last partial TR periods, if any)
%
%	Returns reshaped signal as matrix of size (m,n) where
%		m = height of matrix = tr_length sample size
%		n = width  of matrix = number of complete TR/pulse-echo periods


%new_len = numel(us_table.Voltage) - firstpeak + 1;	% include firstpeak
new_len = numel(voltage) - firstpeak + 1;	% include firstpeak

n_periods = floor(new_len / tr_length);

last_index = firstpeak + n_periods*tr_length - 1;

%M = reshape(us_table.Voltage(firstpeak:last_index), tr_length, n_periods);
M = reshape(voltage(firstpeak:last_index), tr_length, n_periods);


% TODO datatype? can probably use 16bit floats or 32bit to save space (original data is 14bit)
