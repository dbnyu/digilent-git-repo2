function data = convert2ch_voltages(data, v_range1, v_offset1, v_range2, v_offset2)
% Convert a int16 to voltages and append columns to a 2 channel table.
%
%	data = 2 channel AD2 data table w/ int16 values
%	v_range, v_offset = range/offsets for ch1 and ch2 (usually different!)
%					(optional BUT RECOMMENDED! - not sure how consistent the 
%					 defaults are...)
%	TODO need to record these when acquiring data...
%
%	Returns copy of data table with 2 new voltage columns appended.

% TODO can this be re-used for 1ch as well?

% NOTE: These are subject to change/recalibration
%		and are only provided for demo purposes.
%		Likely varies from device to device,
%		with calibration, or even day to day (TODO TBD...)
%	DO NOT RELY ON THESE FOR PRECISE MEASUREMENTS!
DEFAULT_CH1_RANGE = 5.538410;
DEFAULT_CH1_OFFSET = 0.000291;
DEFAULT_CH2_RANGE = 5.546847;
DEFAULT_CH2_OFFSET = -0.000028;



% set defaults for optional args:
if exist('v_range1', 'var') ~= 1
	warning('using approx. default for v_range1')
	v_range1 = DEFAULT_CH1_RANGE; 
end

if exist('v_offset1', 'var') ~= 1
	warning('using approx. default for v_offset1')
	v_offset1 = DEFAULT_CH1_OFFSET;
end

if exist('v_range2', 'var') ~= 1
	warning('using approx. default for v_range2')
	v_range2 = DEFAULT_CH2_RANGE;
end

if exist('v_offset2', 'var') ~= 1
	warning('using approx. default for v_offset2')
	v_offset2 = DEFAULT_CH2_OFFSET;
end


data.ch1_volts = int16signal2voltage(data.ch1_int16, v_range1, v_offset1);
data.ch2_volts = int16signal2voltage(data.ch2_int16, v_range2, v_offset2);

