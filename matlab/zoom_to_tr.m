function zoom_to_tr(x0, x1)
% Zoom (X axis only) into an axis with physical/time units using known indexes
% ie. we know TR = index [1...2000] so we want to use xlim in given time/distance units
% based on these indexes...



ax = gca;
current_xlims = xlim(ax) % this is expected to be arbitrary physical units
current_xdata = get(:q

axx0 = find(current_xlims(1))
axx1 = find(current_xlims(2))
%xlim(
