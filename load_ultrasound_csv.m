function A = load_ultrasound_csv(filename)
% Load an ultrasound CSV file recorded w/ Digilent device

A = readtable(filename);


A = renamevars(A, ["Var1", "Var2", "Var3"], ["Index", "Time", "Voltage"]);

%setColHeading(A, 1, 'Index')
%setColHeading(A, 2, 'Time')
%setColHeading(A, 3, 'Voltage')


fprintf('Read in size:\n')
size(A)
