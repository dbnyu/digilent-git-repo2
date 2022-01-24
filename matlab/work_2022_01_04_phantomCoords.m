function work_2022_01_04_phantomCoords()
% Find distance from transducers to rods in silicone phantom


% TODO these are both approximate:
rTx = 33;	% millimeters, Transducer distance (radius) from center of phantom
rRodCtr = 23; % millimeters, Rod hole center radius from center of phantom

rod_diam =	4.1656; % diameter of phantom rods; APPROXIMATE TODO MEASURE! assuming 8-32" hole size for now...
rod_radius = rod_diam / 2;


% Polar Coordinates [r, theta] with r = mm and theta = radians
%
% Matlab convention for polar coordinates is [theta, rho]
%	theta = angle (radians, range=[-pi, pi])
%	rho = radius
%
% Use [theta,rho] = cart2pol(x,y)
% and [x,y] = pol2cart(theta,rho)
%	to convert polar <-> cartesian
%
% Convention: theta=0 is transducer #1 (with transducers centered between rods)
% and +theta = counterclocwise, looking down at the top.
%

Tx1 = [0,     rTx];
Tx2 = [pi/2,  rTx];
Tx3 = [pi,    rTx];
Tx4 = [-pi/2, rTx];

rod1 = [   pi/4, rRodCtr];
rod2 = [ 3*pi/4, rRodCtr];
rod3 = [-3*pi/4, rRodCtr];
rod4 = [  -pi/4, rRodCtr];


% Tx1 to rod1:
d_tx1_rod1 = polarDist(Tx1, rod1);

% Tx1 to rod2:
d_tx1_rod2 = polarDist(Tx1, rod2);

% the near/far rod distances should be the same for each transducer by symmetry
% TODO use this to test everything
% TODO also assuming perfect angles/rotation on the phantom...


fprintf('\n\n')
fprintf('Phantom Distances:\n')
fprintf('Tx1 to rod1 distance: %f (mm)\n', d_tx1_rod1)
fprintf('   (less rod radius): %f (mm)\n', d_tx1_rod1 - rod_radius)

fprintf('\n\n')

fprintf('Tx1 to rod2 distance: %f (mm)\n', d_tx1_rod2)
fprintf('   (less rod radius): %f (mm)\n', d_tx1_rod2 - rod_radius)
fprintf('\n\n')

pol2cart_vec(rod1)

% plot:
figure;
viscircles([0, 0], rTx);	% phantom boundary
hold on
viscircles(pol2cart_vec(rod1), rod_radius);
viscircles(pol2cart_vec(rod2), rod_radius);
viscircles(pol2cart_vec(rod3), rod_radius);
viscircles(pol2cart_vec(rod4), rod_radius);

transducers = [pol2cart_vec(Tx1); pol2cart_vec(Tx2); pol2cart_vec(Tx3); pol2cart_vec(Tx4)];
plot(transducers(:, 1), transducers(:, 2), '+', 'MarkerSize', 10, 'LineWidth', 3)

axis square tight



end


function c = pol2cart_vec(p)
% Wrwapper for pol2cart tha takes a vector as input.
%	p = [theta, radius] vector

	[x, y] = pol2cart(p(1), p(2));
	c = [x, y];
	
end


function d = polarDist(p1, p2)
% Return Euclidean distance of 2 points in polar coordinates
%
%	d is in the same units as the radius of the points.

	%d = norm(pol2cart(p1(1), p1(2)) - pol2cart(p2(1), p2(2)));
	d = norm(pol2cart_vec(p1) - pol2cart_vec(p2));

end
