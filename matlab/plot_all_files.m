function plot_all_files(path)
% loop over all files in a directory and plot them
% assuming all are 2 channel int16 valued files.
%
%	path = path to folder
%		(must include the wildcard file extension if needed)
%		e.g. 
%		path = '../data/*.m'
%
%	Presents a dialog to 'like' a plot, or skip to the next one
%	This just saves the filename of 'liked' plots 

N_CHANNELS = 2;
INT16 = true;


files = dir(path)';


liked_files = {};
like_count = 0;

for f = files
	fprintf('Loading %s\n', f.name)

	fullpath = fullfile(f.folder, f.name);
	data = load_ultrasound_csv(fullpath, N_CHANNELS, INT16);
	data = convert2ch_voltages(data); % TODO NOTE USING DEFAULTS HERE!


	fig = figure;
	plot(data.Time, data.ch1_volts)
	hold on
	plot(data.Time, data.ch2_volts)
	legend('Ch1 (V)', 'Ch2 (V)')
	title(f.name, 'Interpreter', 'none') % don't format LaTeX underscores
	
	val = questdlg('Like this file or skip to next', ...
			       'Continue?', ...
			       'Like!', 'Skip', 'End', 'Skip' ...
		          )

	if isequal(val, 'Like!')
		like_count = like_count + 1;
		liked_files{like_count} = f.name;
	end

	if isequal(val, 'End')
		break
	end

	close(fig)
end


fprintf('Liked files:\n')
if like_count > 0
	for i = 1:like_count
		fprintf('%s\n', liked_files{i})
	end
else
	fprintf('<none>\n')
end

fprintf('\n\n')
