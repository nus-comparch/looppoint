UBUNTU_VERSION?=18.04
TOOL?=looppoint
#SNIPER_GIT_REPO?="http://snipersim.org/download/6abd19013a9e7ae0/git/sniper.git"
DOCKER_IMAGE?=ubuntu:$(UBUNTU_VERSION)-$(TOOL)
DOCKER_FILE?=Dockerfile-ubuntu-$(UBUNTU_VERSION)
DOCKER_FILES=$(wildcard Dockerfile*)
# For use with --no-cache, etc.
DOCKER_BUILD_OPT?=
# Reconstruct the timezone for tzdata
TZFULL=$(subst /, ,$(shell readlink /etc/localtime))
TZ=$(word $(shell expr $(words $(TZFULL)) - 1 ),$(TZFULL))/$(word $(words $(TZFULL)),$(TZFULL))

export CC := gcc-9
export CXX := g++-9
export SDE_BUILD_KIT := ${PWD}/tools/sde-external-9.0.0-2021-11-07-lin

SNIPER_GIT_REPO?=https://github.com/snipersim/snipersim.git

run:
	docker run --rm -it -v "${PWD}:${PWD}" --user $(shell id -u):$(shell id -g) -w "${PWD}" $(DOCKER_IMAGE)

run-root-cwd:
	docker run --privileged --rm -it -v "${PWD}:${PWD}" --user root -w "${PWD}" $(DOCKER_IMAGE)

run-root:
	docker run --rm -it -v "${HOME}:${HOME}" $(DOCKER_IMAGE)

matrix:
	make -C apps/demo/matrix-omp

dotproduct:
	make -C apps/demo/dotproduct-omp

apps: matrix dotproduct

pinkit:
	@if [ ! -d "tools/pin-3.13-98189-g60a6ef199-gcc-linux" ]; then \
		$(info Downloading Pin) \
		wget -O - https://software.intel.com/sites/landingpage/pintool/downloads/pin-3.13-98189-g60a6ef199-gcc-linux.tar.gz  --no-check-certificate | tar -xf - -z -C tools/ ; \
		cp -r tools/pinplay tools/pin-3.13-98189-g60a6ef199-gcc-linux/extras/ ; \
		patch -d tools -p 0 -i pin_alarms.patch ; \
	fi

sdekit:
	@if [ ! -d "tools/sde-external-9.0.0-2021-11-07-lin" ]; then \
		$(info Downloading SDE kit) \
		wget -O - https://downloadmirror.intel.com/684899/sde-external-9.0.0-2021-11-07-lin.tar.xz  --no-check-certificate | tar -xf - -J -C tools/ ; \
		cp -r tools/pinplay-scripts tools/sde-external-9.0.0-2021-11-07-lin/ ; \
	fi

looppoint: sdekit
	make -C tools/src/Profiler TARGET=ia32
	make -C tools/src/Profiler TARGET=intel64
	make -C tools/src/Drivers TARGET=ia32
	make -C tools/src/Drivers build TARGET=ia32
	make -C tools/src/Drivers TARGET=intel64
	make -C tools/src/Drivers build TARGET=intel64

sniper: pinkit
	@if [ ! -d "tools/sniper" ]; then \
		$(info Downloading Sniper from $(SNIPER_GIT_REPO)) \
		git clone $(SNIPER_GIT_REPO) tools/sniper ; \
	fi
	make -C tools/sniper

tools: looppoint sniper

build: $(DOCKER_FILE).build

# Use a .PHONY target to build all of the docker images if requested
Dockerfile%.build: Dockerfile%
	docker build --build-arg TZ_ARG=$(TZ) $(DOCKER_BUILD_OPT) -f $(<) -t ubuntu:$(subst Dockerfile-ubuntu-,,$(<))-$(TOOL) .

BUILD_ALL_TARGETS=$(foreach f,$(DOCKER_FILES),$(f).build)
build-all: $(BUILD_ALL_TARGETS)

clean:
	rm -f *.pyc *.info.log  *.log
	make -C apps/demo/dotproduct-omp clean
	make -C apps/demo/matrix-omp clean
	make -C tools/src/Profiler clean
	make -C tools/src/Drivers clean
	make -C tools/sniper clean

distclean: clean
	rm -rf tools/pin-3.13-98189-g60a6ef199-gcc-linux tools/sniper results/ tools/sde-external-9.0.0-2021-11-07-lin

.PHONY: build build-all run-root run run-cwd apps sdekit pinkit tools clean distclean
