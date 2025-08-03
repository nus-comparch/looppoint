# LoopPoint Methodology
## Abstract

LoopPoint is a sampling methodology applicable to OpenMP-based multi-threaded applications.
Here, we provide a set of tools and the sources required to replicate the primary experiments 
demonstrated in the [LoopPoint paper](https://alenks.github.io/pdf/looppoint_hpca2022.pdf) 
published at HPCA 2022. The workflow comprises of three parts:
1. profiling the application that enables multi-threaded sampling; 
1. sampled simulation of the selected regions;
1. extrapolation of performance results, and plotting the key results. 

This file describes these parts and how to run them.
 
## Artifact check-list (meta-information)
 
| Parameter                  | Value                                                         |
|:---------------------------|---------------------------------------------------------------|
| Program                    | C++ program and Python/shell scripts                          |
| Compilation                | C++17 compiler                                                |
| Benchmarks                 | Any multi-threaded benchmark suite                            |
| Run-time environment       | Ubuntu 24.04, Docker                                          |
| Hardware                   | x86-based Linux machine                                       |
| Output                     | Plain text, tables                                            |
| Experiments                | Run profiling, run simulations, and run extrapolation scripts |
| Experiment customization   | Benchmarks to verify the methodology, number of threads       |
| Disk space requirement     | &asymp;50 GB                                                  |
| Workflow preparation time  | &asymp;1 day                                                  |
| Experiment completion time | &asymp;1-2 days                                               |
| Publicly available?        | Zenodo (10.5281/zenodo.5667620)                               |
| Code licenses              | MIT, BSD, Intel Open Source License, Academic		         |
 
## Description

### How to access
We use SPEC CPU2017 benchmark suite to evaluate the proposed methodology, *LoopPoint*. In this 
artifact, however, we do not include SPEC CPU2017 binaries and provide demo applications to test
the end-to-end methodology. The setup can be used to replicate any results that we show in the
paper. SDE/Pin kits and Sniper will be downloaded while setting up the tool (see Installation section
for instructions). The artifact is available on Zenodo with DOI 10.5281/zenodo.5667620.

### Hardware dependencies
The tools are developed such that it can run on an x86-based Linux machine. We strongly recommend 
running the artifact using the provided docker file. We expect the size of files generated in the 
profiling stage of LoopPoint to be a few GBs, hence we suggest a minimum free space of 50 GB on the 
machine.

### Software dependencies
- GNU Make
- C++17 build toolchain
- Python3
- Docker

### Data sets
We provide two small parallel applications to test the end-to-end methodology of LoopPoint in a 
reasonable amount of time.
- dotproduct-omp: A demo application that computes the vector dot product using OpenMP
- matrix-omp: A demo application that performs matrix multiplication using OpenMP

## Installation

1. Clone the repository and navigate to the base directory
```
$ git clone https://github.com/nus-comparch/looppoint.git
```
1. Follow the below steps to setup and build the tools
	1. Build the docker image (Note that this is a one-time step.)
	```
	$ make build
	```
	2. Run the docker image
	```
	$ make
	```
	3. Build the demo applications
	```
	$ make apps
	```
	4. Download and build Sniper and LoopPoint tools
	```
	$ make tools
	```
1. These steps should automatically download the required versions of SDE/Pin kit and Sniper

## Experiment workflow

In this section, we describe the steps to generate the results shown in the paper. The
end-to-end methodology of LoopPoint involves several steps. However, we have automated the
whole process so that the user need not run every single step.

In the first stage, the selected benchmark is executed to record it as a pinball in  
`whole_program.<input>` directory. This pinball is then profiled for BBVs making use of DCFG 
information and this is stored in `<basename>.Data` directory. The BBVs are clustered and 
representative region boundaries are identified.

In the following stage, the representative region information is  used  to  launch  region
simulations. When  all  the  region simulations are completed, the runtimes are extrapolated 
and compared  with  the  full  application  run. The obtained error and speedup numbers are
displayed as the final output on the console. All the profiling and simulation results are 
stored in the `results` directory.

The driver script to run an application with LoopPoint is provided below:
```
$ ./run-looppoint.py -h
```

The arguments are defined as follows:
* `-p` or `--program`: program to be executed, supplied in the format `<suite>-<application>-<input-num>` \
Multiple programs can be submitted as comma-separated inputs \
_Default:_ `demo-matrix-1`
* `-n` or `--ncores`: num of threads \
_Default:_ `8`
_Note:_ The demo app has three inputs for test input class and is hard set to work for 8 threads.
* `-i` or `--input-class`: input class \
_Default:_ `test`
* `-w` or `--wait-policy`: omp wait policy \
_Options:_ `passive`, `active` \
_Default:_ `passive`
* `-c` or `--custom-cfg`: Run a workload of interest using cfg-file in the current directory \
_Note:_ Cannot be used alongside `-p` or `--program`. More details [here](#running-custom-workloads)
* `--force`: Start a new set of end-to-end run (**Warning**: The full application simulation can take a long time)
* `--reuse-profile`: Reuse the default profiling data (used along with `--force`)
* `--reuse-fullsim`: Reuse the default full program simulation (used along with `--force`)
* `--no-validate`: Skip full program simulation and display only the sampled simulation result (used along with `--force`)
* `--no-flowcontrol`: Disable thread flowcontrol during profiling
* `--use-pinplay`: Use PinPlay instead of SDE for profiling
* `--pinball-analysis`: Use deterministic analysis with pinballs instead of binary runs
* `--native`: Run the application natively
Note that SPEC applications and default results are not included in the open version.

###### Usage Examples
```
./run-looppoint.py -p demo-matrix-1 -n 8 --force --no-validate
```
will start a new set of end-to-end run for `demo-matrix-1` program with `8` cores, using `passive` wait policy and `test` inputs \
without running the full program simulation.

```
./run-looppoint.py -p demo-dotproduct-1 -w active -i test --force
```
will start a new set of end-to-end run for `demo-matrix-2` program with `8` cores, using `active` wait policy and `test` inputs

```
/path/to/looppoint/run-looppoint.py -n 8 -c 603.bwaves-s.1.cfg --force
```
will start a new set of end-to-end run for a custom workload `603.bwaves-s.1` program with `8` cores, using the config file `603.bwaves-s.1.cfg`

###### Running Custom Workloads
Integrating a new benchmark suite with the LoopPoint setup requires some modifications in the scripts. However, running LoopPoint for an application from it's own directory is straightforward. The flag `--custom-cfg` accepts a config file of the application that the user wants to run. A typical config file (`603.bwaves_s.1.cfg`) of an application (`603.bwaves_s.1`) looks like this:
```
[Parameters]
program_name: bwaves-s
input_name: 1
command: ./speed_bwaves.icc18.0.gO2avx bwaves_1 < bwaves_1.in
```
It is necessary to keep the above three fields (program_name, input_name, command) in the config file of the application for it to work with the infrastructure. We also recommend keeping all necessary binaries and the respective inputs of the application in the same directory as that of the config file, as this is where `run-looppoint.py` script looks for them. The results of the sampling run are stored in the same application directory. Note that, this flag cannot be used along with the flag `--program` as `--program` runs a program that is already integrated with the LoopPoint workflow, whereas `custom-cfg` runs an application of choice. 
```
/path/to/looppoint/run-looppoint.py -n 8 -c 603.bwaves_s.1.cfg -w active --force
```
## Evaluation and expected results
To replicate the results shown in the LoopPoint paper, it is necessary to run each of the applications in SPEC CPU2017 benchmark suite.
The users can add any multi-threaded application in a similar fashion (see how the demo applications are set up) and
test LoopPoint infrastructure there. Note that, launching a new set of end-to-end evaluation is long-running for large applications
as the full application simulation can take a long time.

The evaluation of LoopPoint is done for SPEC CPU2017 applications that consume train inputs. While using both 
active and passive wait policies, LoopPoint has an average absolute error of &asymp;2.3% in predicting the 
performance metrics of multi-threaded applications using sampled simulation achieving speedups of up to 800x.

