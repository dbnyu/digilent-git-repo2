function data = load_and_convert_us_csv(csv_file, nchannels, vconv_file)
	% Load an int16 ultrasound CSV file and voltage conversion parameters
	% convert to voltages & return complete table.
	%
	%	csv_file = data file (int16 format expected)
	%	nchannels = number of channels to read in (int)
	%	vconv_file = voltage conversion parameters (optional)
	%					if ignored; assumes standard naming format & looks for the 
	%					<...>_vconv.csv file automatically.
	%
	%					Assumes file format only has 2 underscores:
	%					20220121-180351_red2blue-SHIFT_vconv.csv
	%
	%	Both file inputs must be complete paths (if specified).
	%
	%	Returns Table.

	if exist('vconv_file', 'var') ~= 1

		[path, fname, extension] = fileparts(csv_file);
		
		splitname = split(fname, '_');

		newname = [splitname{1}, '_', splitname{2}, '_vconv.csv']; % put the parts back together
		vconv_file = fullfile(path, newname);
		fprintf('Looking for default vconv file: %s\n', vconv_file)
	end

	data = load_ultrasound_csv(csv_file, nchannels, true);

	vconv_info = load_ad2_vconv_params(vconv_file);

	data = convert2ch_voltages(data, ...
                               vconv_info.ch1_v_range, ...
                               vconv_info.ch1_v_offset, ...
                               vconv_info.ch2_v_range, ...
                               vconv_info.ch2_v_offset);
