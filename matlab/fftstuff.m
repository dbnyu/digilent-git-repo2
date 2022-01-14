% From Chris:
%
%	NOTES:
%		- FFT output length (big N) is arbitrary; best for power of 2 (multiple)?
%			- ~2x input length is a good start
%		- this includes an exponential decay (the loops) which can be ignored.
%		- can ignore the negative half of the frequency spectrum

%load tunedlargecoilonlyhighFHZ.dat; 
%HX=tunedlargecoilonlyhighFHZ;
%load HX.dat;
%load HY.dat;
%n=104000; N=65536*2;

HX = sig;
n=length(sig); N=65536*2;
t =	t10mhz;

% exponential decay:
deca(n)=0;t(n)=0;Hy(n)=0;Hx(n)=0;
for I=1:n, 
    %t(I)=HX(I,1); 
	Hx(I)=HX(I);
    %t(I)=HY(I,1); Hy(I)=HY(I,2);
end
for(I=1:n), 
    decaY(I)=exp(0*t(I))*Hy(I);
    decaX(I)=Hx(I); 
end

plot(t,decaY);
figure; plot(t,decaX);
AY=fft(decaY,N);
AX=fft(decaX,N);

PAY=AY.*conj(AY)/N;
PAX=AX.*conj(AX)/N;
f=1/t(1)*(0:(N/2-1))/N;

figure; semilogy(f,PAY(1:N/2));
figure; semilogy(f,PAX(1:N/2));

%n=1000; N=65536*2;
%AV12=fft((V1+V2),N);
%PAV12=AV12.*conj(AV12)/N;
%f=1/dt*(0:(N/2-1))/N;
%figure;plot(f,PAV12(1:N/2));

