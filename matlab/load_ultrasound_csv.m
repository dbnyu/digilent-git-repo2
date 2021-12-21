function A = load_ultrasound_csv(filename, Nchannels, int16)
% Load an ultrasound CSV file recorded w/ Digilent device
%	filename = path to file
%	Nchannels = # of channels (1 or 2)
%	int16	= True if data is raw int16 or not


int16

if exist('int16', 'var') ~= 1
	fprintf('No voltage format specified; assuming proper Voltages\n')
	int16 = false;
end

fprintf('Loading %s\n', filename)
A = readtable(filename);

if int16
	v_header = 'int16';
else
	v_header = 'volts';
end


ch1header = ['ch1_', v_header];
ch2header = ['ch2_', v_header];	% not used in 1ch case


if Nchannels == 1
	A = renamevars(A, ["Var1", "Var2", "Var3"], ["Index", "Time", ch1header]);
else
	A = renamevars(A, ["Var1", "Var2", "Var3", "Var4"], ["Index", "Time", ch1header, ch2header]);
end


fprintf('Read in size:\n')
size(A)
