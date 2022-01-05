% Plot multiple files to compare them
% plots all ch1's and ch2's separately to compare like-to-like


C_WATER = 1482.3; % meters/second speed of sound in water		 
% from https://itis.swiss/virtual-population/tissue-properties/database/acoustic-properties/speed-of-sound/


filedir = '..\2022-01-04-phantomWithGel';

files = {'20220104-144340_red2blueSquare1H.csv', ...
		 '20220104-144447_red2blueSquare1Ms.csv', ...
		 %'20220104-150117_red2blueSquare1H_2p5V.csv' ...		% TODO change 2nd underscore
		 };

%files = {'20220104-145014_red2blueSine10x.csv', ...
%		 '20220104-145107_red2blueSine3x.csv', ...
%		 '20220104-145330_red2blueSine1x.csv', ...
%		 };


%files = {%'20220104-144201_red2blueSquare1H.csv', ...
%		 %'20220104-144246_red2blueSquare1H.csv', ...
%		 %'20220104-144335_red2blueSquare1H.csv', ...
%		 '20220104-144340_red2blueSquare1H.csv', ...
%		 %'20220104-144423_red2blueSquare1Ms.csv', ...
%		 %'20220104-144441_red2blueSquare1Ms.csv', ...
%		 '20220104-144447_red2blueSquare1Ms.csv', ...
%		 %'20220104-144503_red2blueSquare1MsTouchWires.csv', ...
%		 %'20220104-144536_red2blueSquare1MsTouchRedTdxCloth.csv', ...
%		 %'20220104-144830_red2blueSine10x.csv', ...
%		 %'20220104-144857_red2blueSine10x.csv', ...
%		 %'20220104-144921_red2blueSine10x.csv', ...
%		 %'20220104-144936_red2blueSine10x.csv', ...
%		 %'20220104-145004_red2blueSine10x.csv', ...
%		 %'20220104-145009_red2blueSine10x.csv', ...
%		 '20220104-145014_red2blueSine10x.csv', ...
%		 %'20220104-145042_red2blueSine3x.csv', ...
%		 %'20220104-145057_red2blueSine3x.csv', ...
%		 %'20220104-145103_red2blueSine3x.csv', ...
%		 '20220104-145107_red2blueSine3x.csv', ...
%		 %'20220104-145123_red2blueSine1x.csv', ...
%		 %'20220104-145129_red2blueSine1x.csv', ...
%		 %'20220104-145144_red2blueSine1x.csv', ...
%		 %'20220104-145148_red2blueSine1x.csv', ...
%		 '20220104-145330_red2blueSine1x.csv', ...
%		 %'20220104-150012_red2blueSquare1HDECREASING.csv', ...
%		 '20220104-150117_red2blueSquare1H_2p5V.csv' ...		% TODO change 2nd underscore
%		 };

% NOTE - assuming same voltage conversion parameters for all files (checked for this dataset)
vconv_info = load_ad2_vconv_params(fullfile(filedir, '20220104-144340_red2blueSquare1H_params.csv'));

legends = {};
fnames = {};
data = {};
for i = 1:numel(files)

	fnames{i} = files{i};
	tmp1 = split(fnames{i}, '_');
	tmp2 = split(tmp1{2}, '.');
	legends{i} = tmp2{1};
	

	fprintf('%d: %s\t%s\n', i, files{i}, legends{i})

	data{i} = load_ultrasound_csv(fullfile(filedir, files{i}), 2, true);
	data{i} = convert2ch_voltages(data{i}, ...
								  vconv_info.ch1_v_range, ...
								  vconv_info.ch1_v_offset, ...
								  vconv_info.ch2_v_range, ...
								  vconv_info.ch2_v_offset);

	if i > 1
		assert(sum(data{i}.Time - data{i-1}.Time) == 0, 'Time axes dont match.')
	end

end

%legends{end} = [legends{i} ' 2.5V'];


% NOTE - distance does NOT reset for each TR - so only differences are useful here:
%		 it should be accurate for the FIRST TR though
%		 But also note that there's an offset (T=0 is NOT the first peak due to pre-roll in acquisition)
%`			so in either case differenes are best
distance = C_WATER * data{1}.Time;	% (meters) NOTE assuming timescales are the same!
distance = 1000 * distance; % convert to mm




figure;


% Plot Ch. 1
for i = 1:numel(data)
	fprintf('%d: %s\t%s\n', i, files{i}, legends{i})

	%plot(data{i}.Time, data{i}.ch1_volts, '.-')
	plot(distance, data{i}.ch1_volts, '.-')

	hold on
end
title('Ch. 1 (Wavegen Direct)')
%xlabel('Time (s)')
xlabel('Distance (mm)')
ylabel('Amplitude (V)')
legend(legends)


% TODO NOTE - a uniform distance axis is not really correct (should reset to 0 on each TR)...
% need to do modulo time... not sure if that works for an axis (probably needs to be monotonic)
% TODO differences (ie. d1 - d0) should be accurate though...

%x_water = C_WATER * data{1}.Time; % this is assuming all timescales are the same - get actual X axis values

% % TODO try this - https://www.mathworks.com/matlabcentral/discussions/highlights/134586-new-in-r2021a-limitschangedfcn
%ax_t = gca;	% time axis
%
%ax_t_xlims = xlim(ax_t);
%%ax_t_ticks = xticks(ax_t)
%
%ax_d_xlims = ax_t_xlims * C_WATER; % compute the 'distance' min/max xlims
%
%ax_d_position = ax_t.Position + [0 0.1 0 0];
%ax_d_position(4) = 1e-12; % set height to be negligible
%
%ax_d = axes('Position', ax_d_position);	% distance axis
%
%% full meters:
%%set(ax_d, 'xlim', ax_d_xlims)
%%xlabel(ax_d, 'Distance (m)')
%
%% millimeters:
%set(ax_d, 'xlim', 1000*ax_d_xlims)
%xlabel(ax_d, 'Distance (mm)')
%
%linkaxes([ax_t, ax_d], 'x')

hold off

% Plot Ch. 2
figure;
for i = 1:numel(data)
	fprintf('%d: %s\t%s\n', i, files{i}, legends{i})

	%plot(data{i}.Time, data{i}.ch2_volts, '.-')
	plot(distance, data{i}.ch2_volts, '.-')
	hold on
end
title('Ch. 2 (180^\circ Receiver)')
%xlabel('Time (s)')
xlabel('Distance (mm)')
ylabel('Amplitude (V)')
legend(legends)
