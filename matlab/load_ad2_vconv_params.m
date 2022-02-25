function A = load_ad2_vconv_params(filepath)
% Load a CSV file of scope voltage conversion parameters
%	also works for any 1-row metadata files
%
%	filepath = path to file
%	
%	Expects 1 row of headers and 1 row of (scalar) data per column.
%
%	TO VIEW NICELY: rows2vars(A)


A = readtable(filepath);
