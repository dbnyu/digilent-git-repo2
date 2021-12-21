function plot_M_mode(M, ignore_rows, title_str)
%
%	M = M-mode ultrasound matrix
%	ignore_rows = # of rows at top of matrix to ignore for colormap (e.g. excitation pulse)
%					still displays the top rows, just ignores them when setting caxis
%					(optional - default = 1, ie. include all rows)
%	title_str	= string for title (optional)

figure
imagesc(M)
colormap gray
hc = colorbar();
ylabel(hc, 'Voltage (V)')

if exist('ignore_rows', 'var') ~= 1
	ignore_rows = 1;
end

if exist('title_str', 'var') ~= 1
	title_str = 'M-Mode Ultrasound';
end

cmin = min(M(ignore_rows:end, :), [], 'all');
cmax = max(M(ignore_rows:end, :), [], 'all');
caxis([cmin, cmax])

title(title_str)
xlabel('Repetition Index') % TODO display actual TR time
ylabel('Echo Time Index') % TODO display actual time on Y axis
