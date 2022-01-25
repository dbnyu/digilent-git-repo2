function [f, pf] = plot_fft(t, x, start_idx, end_idx, title_str)
% Plot frequency spectrum of signal
%
%	t = time values
%	x = signal values
%	start_idx, end_idx = start/end indexes if using a subset of signal (optional)
%		default = use whole time series
%	title_str = title for plot
%
%	TODO - do we need full t vector, or just a single dt value?

if exist('start_idx', 'var') ~= 1
	start_idx = 1;
end

if exist('end_idx', 'var') ~= 1
	end_idx = length(x);
end

if exist('title_str', 'var') ~= 1
	title_str = 'FFT Plot';
end

% This should be end - start + 1:
x = x(start_idx:end_idx);
t = t(start_idx:end_idx);
%n_samples = end_idx - start_idx + 1; % # of samples in TIME SERIES
n_samples = length(x);

% TODO this should be a power of 2!!!
% custom fft output length:
%N_freqs = n_samples * 2 % # of frequency samples (incuding negative freqs)
%pf = fft(x, N_freqs); % pf = frequency 'power' == Y axis of FFT plot

% Trying default (same length as input signal):
pf = fft(x); % pf = frequency 'power' == Y axis of FFT plot
N_freqs = length(pf);


pf = pf.*conj(pf) / N_freqs;	% convert back to Real values & normalize (?)

pf = pf(1:N_freqs/2);	% take positive frequency values


dt = mean(diff(t));

% TODO which one of these is right?
%f=1/t(1) * (0:(N_freqs/2-1))/N_freqs;
f = 1/dt * (0:(N_freqs/2-1))/N_freqs;	% this seems to match matlab example


figure;
%plot(t, x)
plot(x)
title('Time Series Signal')
xlabel('index (of subset)')
ylabel('Voltage (V?)')

figure; 
%semilogy(f, pf(1:N_freqs/2));
%plot(f, pf(1:N_freqs/2));
plot(f, pf)
title(title_str)
xlabel('Freq. (Hz)')
ylabel('Intensity (?)')
