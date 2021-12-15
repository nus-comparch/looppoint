CC ?= gcc
CXX ?= g++

all: matrix-omp

matrix-omp: matrix-omp.cpp matrix-omp.h matrix-omp-init.cpp
	$(CXX) -g -O3 -fopenmp -o matrix-omp matrix-omp-init.cpp matrix-omp.cpp --static
	ln -s matrix-omp base.exe

clean:
	rm -f ./matrix-omp ./*.o ./*.S ./base.exe

.PHONY: clean
