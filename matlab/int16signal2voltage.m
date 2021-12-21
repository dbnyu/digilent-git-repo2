function v = int162voltage(data_int16, v_range, v_offset)
%	Convert AD2 int16 data to float voltages.
%
%	Requires *actual* v_range and v_offset read from scope
%	which are usuall NOT exactly equal to 5.0 and 0.0 V (respectively)
%	but those work as approximations.
%
%	data_int16 = single column vector (Nx1) of raw int16 values from scope
%				(assumed that type is already 'matlab double'; 
%				 no int->float conversion is done here at the moment.)
%	v_range = voltage range setting from scope (scalar float)
%	v_offset = voltage offset setting from scope (scalar float)
%
%
%	Returns column vector (Nx1) of float voltages.


v = (data_int16 * v_range / 65536) + v_offset;
