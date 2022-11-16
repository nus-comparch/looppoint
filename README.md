# LoopPoint: Checkpoint-driven Sampled Simulation for Multi-threaded Applications (HPCA 2022)
## Abstract

In this toolchain, we provide the source code needed to replicate the primary experiments 
demonstrated in the LoopPoint paper. The artifact provides scripts that comprise three parts:
1. profiling the application that enables multi-threaded sampling; 
1. sampled simulation of the selected regions;
1. extrapolation of performance results, and plotting the key results. 

This file describes these parts and how to run them.
 
## Artifact check-list (meta-information)
 
| Parameter                  | Value                                                         |
|:---------------------------|---------------------------------------------------------------|
| Program                    | C++ program and Python/shell scripts                          |
| Compilation                | C++11 compiler                                                |
| Benchmarks                 | Any multi-threaded benchmark suite                            |
| Run-time environment       | Ubuntu 18.04, Docker                                          |
| Hardware                   | x86-based Linux machine                                       |
| Output                     | Plain text, tables                                            |
| Experiments                | Run profiling, run simulations, and run extrapolation scripts |
| Experiment customization   | Benchmarks to verify the methodology, number of threads       |
| Disk space requirement     | &asymp;50 GB                                                  |
| Workflow preparation time  | &asymp;1 day                                                  |
| Experiment completion time | &asymp;1-4 weeks                                              |
| Publicly available?        | Zenodo (10.5281/zenodo.5667620)                               |
| Code licenses              | Academic and Proprietary                                      |
 
## Description

### How to access
We use SPEC CPU2017 benchmark suite to evaluate the proposed methodology, *LoopPoint*. In this 
artifact, however, we do not include SPEC CPU2017 binaries and provide a demo application to test
the end-to-end methodology. The setup can be used to replicate any results that we show in the
paper. SDE/Pin kits and Sniper will be downloaded while setting up the artifact (see Installation section
for instructions). The tool binaries are provided that works with Intel SDE/Pin. The artifact is available 
on Zenodo with DOI 10.5281/zenodo.5667620.

### Hardware dependencies
The artifact is developed such that it can run on an x86-based Linux machine. We strongly recommend 
running the artifact using the provided docker file. We expect the size of files generated in the 
profiling stage of LoopPoint to be a few GBs, hence we suggest a minimum free space of 50 GB on the 
machine.

### Software dependencies
- GNU Make
- C++11 build toolchain
- Python
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
1. Follow the below steps to setup and build the artifact once you have the Sniper gitid
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

The tool to read, evaluate, and display the key results for an application is provided below:
```
$ ./run-looppoint.py -h
```

The arguments are defined as follows:
* `-p` or `--program`: program to be executed, supplied in the format `<suite>-<application>-<input-num>` \
Multiple programs can be submitted as comma-separated inputs \
_Default:_ `demo-dotproduct-1`
* `-n` or `--ncores`: num of threads \
_Default:_ `8`
_Note:_ The demo app has three inputs for test input class and is hard set to work for 8 threads.
* `-i` or `--input-class`: input class \
_Default:_ `test`
* `-w` or `--wait-policy`: omp wait policy \
_Options:_ `passive`, `active` \
_Default:_ `passive`
* `-c` or `--custom-cfg`: Run a workload of interest using cfg-file in the current directory \
_Note:_ Cannot be used alongside `-p` or `--program`.
* `--force`: Start a new set of end-to-end run (**Warning**: The full application simulation can take a long time)
* `--reuse-profile`: Reuse the default profiling data (used along with `--force`)
* `--reuse-fullsim`: Reuse the default full program simulation (used along with `--force`)
* `--no-flowcontrol`: Disable thread flowcontrol during profiling
* `--use-pinplay`: Use PinPlay instead of SDE for profiling
* `--native`: Run the application natively
Note that SPEC applications and default results are not included in the open version.

###### Usage Examples
```
./run-looppoint.py -p demo-dotproduct-1 -n 8 --force
```
will start a new set of end-to-end run for `demo-dotproduct-1` program with `8` cores, using `passive` wait policy and `test` inputs

```
./run-looppoint.py -p demo-matrix-2 -w active -i test --force
```
will start a new set of end-to-end run for `demo-matrix-2` program with `8` cores, using `active` wait policy and `test` inputs

###### Running Custom Workloads
Integrating a new benchmark suite with the LoopPoint setup requires some modifications in the scripts. However, running LoopPoint for an application from it's own directory is straightforward. The flag `--custom-cfg` accepts a config file of the application that the user wants to run. A typical config file (matmul.0.cfg) of an application (matmul-omp) looks like this:
```
[Parameters]
program_name: matmul-omp
input_name: 1
command: ./matmul 100 8
```
It is necessary to keep the above three fields (program_name, input_name, command) in the config file of the application for it to work with the infrastructure. We also recommend keeping all necessary binaries and the respective inputs of the application in the same directory as that of the config file, as this is where `run-looppoint.py` script looks. The results of the sampling run are stored in the same application directory. Note that, this flag cannot be used along with the flag `--program` as `--program` runs a program that is already integrated with the LoopPoint workflow, whereas `custom-cfg` runs an application of choice. 
```
/path/to/looppoint/run-looppoint.py -n 8 -c matmul.0.cfg --force
```
## Evaluation and expected results
To replicate the results shown in the LoopPoint paper, it is necessary to run each of the applications in SPEC CPU2017 benchmark suite.
The users can add any multi-threaded application in a similar fashion (see how the demo applications are set up) and
test LoopPoint infrastructure there. Note that, launching a new set of end-to-end evaluation is long-running for large applications
as the full application simulation can take a long time.

The evaluation of LoopPoint is done for SPEC CPU2017 applications that consume train inputs. While using both 
active and passive wait policies, LoopPoint has an average absolute error of &asymp;2.3% in predicting the 
performance metrics of multi-threaded applications using sampled simulation achieving speedups of up to 800x.

