% See plot_compare.m too
% This plots 1 file at a time. (ch1 and ch2 together.)



C_WATER = 1482.3; % meters/second speed of sound in water		 

%filedir = '..\2022-01-04-phantomWithGel';
%
%files = {'20220104-144340_red2blueSquare1H.csv', ...
%		 '20220104-144447_red2blueSquare1Ms.csv', ...
%		 %'20220104-150117_red2blueSquare1H_2p5V.csv' ...		% TODO change 2nd underscore
%		 };

%files = {'20220104-145014_red2blueSine10x.csv', ...
%		 '20220104-145107_red2blueSine3x.csv', ...
%		 '20220104-145330_red2blueSine1x.csv', ...
%		 };


%file = %'20220104-144201_red2blueSquare1H.csv' 
%file = %'20220104-144246_red2blueSquare1H.csv' 
%file = %'20220104-144335_red2blueSquare1H.csv' 
file = '20220104-144340_red2blueSquare1H.csv' 
%file = %'20220104-144423_red2blueSquare1Ms.csv' 
%file = %'20220104-144441_red2blueSquare1Ms.csv' 
%%file = '20220104-144447_red2blueSquare1Ms.csv' 
%file = %'20220104-144503_red2blueSquare1MsTouchWires.csv' 
%file = %'20220104-144536_red2blueSquare1MsTouchRedTdxCloth.csv' 
%file = %'20220104-144830_red2blueSine10x.csv' 
%file = %'20220104-144857_red2blueSine10x.csv' 
%file = %'20220104-144921_red2blueSine10x.csv' 
%file = %'20220104-144936_red2blueSine10x.csv' 
%file = %'20220104-145004_red2blueSine10x.csv' 
%file = %'20220104-145009_red2blueSine10x.csv' 
%%file = '20220104-145014_red2blueSine10x.csv' 
%file = %'20220104-145042_red2blueSine3x.csv' 
%file = %'20220104-145057_red2blueSine3x.csv' 
%file = %'20220104-145103_red2blueSine3x.csv' 
%%file = '20220104-145107_red2blueSine3x.csv' 
%file = %'20220104-145123_red2blueSine1x.csv' 
%file = %'20220104-145129_red2blueSine1x.csv' 
%file = %'20220104-145144_red2blueSine1x.csv' 
%file = %'20220104-145148_red2blueSine1x.csv' 
%%file = '20220104-145330_red2blueSine1x.csv' 
%file = %'20220104-150012_red2blueSquare1HDECREASING.csv' 
%%file = '20220104-150117_red2blueSquare1H_2p5V.csv' 		% TODO change 2nd underscore


basename = split(file, '.');
basename = basename{1}
vconv_param_file = [basename '_param.csv'];

% TODO update to vconv_param_file  (doesn't exist for all files from 1/4 though).
vconv_info = load_ad2_vconv_params(fullfile(filedir, '20220104-144340_red2blueSquare1H_params.csv'));


data = load_ultrasound_csv(fullfile(filedir, file), 2, true);
data = convert2ch_voltages(data, ...
						  vconv_info.ch1_v_range, ...
						  vconv_info.ch1_v_offset, ...
						  vconv_info.ch2_v_range, ...
						  vconv_info.ch2_v_offset);

data(1:10, :)


distances = C_WATER * data.Time; % meters
distances = 1000*distances; % mm

% squash the excitation peaks:
ratio = max(abs(data.ch2_volts)) / max(abs(data.ch1_volts));
% TODO could select an arbitrary height threshold ie. 1.5* max(ch2) 
% TODO or adjust ratio so that peaks are a little higher
ind2squash =  abs(data.ch1_volts) > max(abs(data.ch2_volts));
n_squashed = sum(ind2squash); 
fprintf('Squashing %d points (%.2f %%)\n', n_squashed, 100*n_squashed/numel(data.ch1_volts))

data.ch1_volts(ind2squash) = 1.5 * ratio * data.ch1_volts(ind2squash);


figure;
plot(distances, data.ch1_volts, '-')
hold on
%yyaxis right	% this doesn't align the zeros...

plot(distances, data.ch2_volts, '-')
legend('Ch. 1 (V)', 'Ch. 2 (V)')
xlabel('Distance (mm, TR delays omitted!)')
ylabel('Amplitude (V)')





