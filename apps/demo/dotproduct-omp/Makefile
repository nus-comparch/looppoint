#Copyright (C) 2022 Intel Corporation
#SPDX-License-Identifier: BSD-3-Clause
CC ?= gcc
CXX ?= g++

all: dotproduct-omp

dotproduct-omp: dot_product_openmp.cpp
	$(CXX) -g -O3 -fopenmp -o dotproduct-omp dot_product_openmp.cpp 
	ln -s dotproduct-omp base.exe

clean:
	rm -rf ./dotproduct-omp ./*.o ./*.S ./base.exe *out *.info.* *.txt 

.PHONY: clean
