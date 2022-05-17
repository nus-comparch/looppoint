#!/usr/intel/pkgs/python/3.6.0/bin/python
# -*- coding: utf-8 -*-

import gzip
import logging
import argparse
import xml.dom.minidom as dom
import sys
import subprocess
import configparser
from shutil import copyfile
from os import devnull
from pathlib import Path

import LitUpLib
import Injections


##### CONSTANTS #####
PROG_NAME                   = Path(__file__).name
PROG_PATH                   = Path(__file__).resolve().parent
MEM_IMAGE_ASM_FILENAME      = "memory_image.asm"
ARCH_STATE_ASM_FILENAME     = "arch_state.asm"
BOOT_ASM_FILENAME           = "boot_global.asm"
INJECTIONS_ASM_FILENAME     = "injections.asm"
THREAD_TEMPLATE_FILE        = "boot_thread_template.asm"
AMX_TEMPLATE_FILE           = "xrstor_thread_amx_image.asm"
OBJ_DEFAULT_FILENAME        = "baremetal"


##### GLOBAL DATA STRUCTURES #####
WRITE_SYSCALL_NUMBER            = 1     # write()           syscall number in Linux
CLOCK_GETTIME_SYSCALL_NUMBER    = 228   # clock_gettime()   syscall number in Linux


##### MAIN #####
arg_parser = argparse.ArgumentParser(description='''LitUp is a tool which takes a LIT (Long Instruction Trace) 
and converts it to a bootable bare-metal ASM file (in iASM format). Such LIT usually includes two files: 
AMI file that represents that physical memory image of the trace and ARCH.XML file that represents a snapshot 
of the processor state and capabilities''')

arg_parser.add_argument('--ami',
                        help='The AMI file')
arg_parser.add_argument('--arch-xml',
                        help='The ARCH.XML file')
arg_parser.add_argument('-o', '--output',
                        default=OBJ_DEFAULT_FILENAME,
                        help='The resulting output filename (default: %(default)s) without extension. The file extension is either ASM or 32.OBJ if --iasm flag was used.')
arg_parser.add_argument('-n', '--num-instructions',
                        default=None,
                        help='Number of instructions to execute on each thread. This overrides any <inscount> value in the ARCH.XML. The behavior is achieved using PERFMON counters and #PMI for stopping.')
arg_parser.add_argument('--iasm',
                        default=None,
                        metavar='"IASM COMMAND-LINE"',
                        help='iASM command line to compile the resulting ASM files to a single 32.OBJ. '
                        'Note: Command line should not include the ASM filename input - which is automatically added. '
                        'The result is '+OBJ_DEFAULT_FILENAME+'.32.obj (unless used with "-o" flag). '
                        'Usage Example: --iasm "$CAD_ROOT/iASM/latest/secure/em64t_SLES11/iasm -b all -32 -max_addr 52"')
arg_parser.add_argument('-v', '--verbosity',
                        action = "store_true",
                        help='Output additional debug info')

### Advanced ###
arg_parser.add_argument('--pmi-count-os-instr',
                        default=False,
                        action = "store_true",
                        help='Whether to count also OS (ring-0) instructions when terminating with #PMI. Should be used when the LIT has ring-0 code and termination is not by specific LIP. (default: %(default)s).')
arg_parser.add_argument('--load-syscall-msrs',
                        default=False,
                        action = "store_true",
                        help='Whether to load the 0xC00000XX MSRs to allow the LIT to use its system call handlers or override it with LitUp handling (default: %(default)s).')
arg_parser.add_argument('--load-idt',
                        default=False,
                        action = "store_true",
                        help='Whether to load the IDT to allow the LIT to use its own handlers or override it with LitUp handling (default: %(default)s).')
arg_parser.add_argument('--real-clock-gettime',
                        default=None,
                        metavar='"SDE_DEBUGTRACE"',
                        help='When supplied, "clock_gettime" system calls (i.e.: SYSCALL where EAX=228) side effects are not recorded and injected, '
                        'but instead a the processor TSC is read, and the result is converted to time (seconds and nano seconds) and returned back to the user code. '
                        'The argument needs SDE debug trace file to detect the relevant system calls and their side effects to avoid. '
                        'Note: This can break playback determinism and even fail execution if code is branching to unrecorded code according to the time results.')
arg_parser.add_argument('--config-file',
                        default=None,
                        metavar='CONFIG_FILE.INI',
                        help='Configuration file which can be used to provide multiple LITs. Cannot be provided with other inputs.')
arg_parser.add_argument('--lit-folder',
                        default=None,
                        metavar='PATH_WITH_LITS',
                        help='Path to a folder with AMI and ARCH.XML files, LitUp will pick-up all the traces in the folder. Cannot be provided with other inputs.')

args = arg_parser.parse_args()


# Verbosity
verbosity_level = logging.INFO
if (args.verbosity):
    verbosity_level = logging.DEBUG
logging.basicConfig(format = "{}  %(levelname)-7s: %(message)s".format(PROG_NAME), level = verbosity_level)


# Default output file name
if args.output.lower().endswith('.32.obj'):
    args.output = args.output[:-7]
if args.output.lower().endswith('.asm') or args.output.lower().endswith('.obj'):
    args.output = args.output[:-4]


# Some sanity checks
if (args.ami and not args.arch_xml) or (args.arch_xml and not args.ami):
    logging.error('You must always provide "--ami" and "--arch-xml" switches together')
    exit(1)
if args.ami and args.config_file:
    logging.error('You cannot provide both "--ami" and "--config-file" switches')
    exit(1)
if args.ami and args.lit_folder:
    logging.error('You cannot provide both "--ami" and "--lit-folder" switches')
    exit(1)
if args.config_file and args.lit_folder:
    logging.error('You cannot provide both "--config-file" and "--lit-folder" switches')
    exit(1)


# Load the config file or take it from folder, or from cmdline
config = configparser.ConfigParser()
if args.config_file:
    if not Path(args.config_file).exists():
        logging.error('File not found: {}'.format(args.config_file))
        exit(1)
    config.read(args.config_file)
    num_lits = int(config['DEFAULT']['NumLits'])
    for i in range(num_lits):
        arch_dom = dom.parse(config['Lit'+str(i)]['archxml'])
        num_cpus = int(arch_dom.getElementsByTagName("num_cpus")[0].firstChild.nodeValue)
        if num_lits > 1 and num_cpus > 1:
            logging.error("NumLits > 1 in config file can only support single threaded LITs, but '{}' has <num_cpus> bigger than 1".format(config['Lit0']['archxml']))
            exit(1)
    num_cpus = num_lits # currently we can only merge single threaded LITs so num CPUs is num LITs
    logging.info("More than one LIT given, setting num_cpus artificially to {}".format(num_cpus))
elif args.lit_folder:
    num_lits = 0
    num_cpus = 0
    for ami in Path(args.lit_folder).glob('*.ami'):
        lit = 'Lit'+str(num_lits)
        config[lit] = {}
        config[lit]['ami'] = str(ami.resolve())
        config[lit]['archxml'] = str((Path(ami).parent / Path(Path(ami).stem + ".arch.xml")).resolve())
        arch_dom = dom.parse(config[lit]['archxml'])
        num_cpus += int(arch_dom.getElementsByTagName("num_cpus")[0].firstChild.nodeValue)
        num_lits += 1
    if num_lits == 0:
        logging.error("No LITs (AMI and ARCH.XML files) found in the given --lit-folder '{}'".format(args.lit_folder))
        exit(1)
    logging.info("Found {} LITs (AMI and ARCH.XML files) in the given folder".format(num_lits))
    if num_lits > 1 and num_cpus > num_lits:
        logging.error("More than one LIT in the given --lit-folder but at least one of the LITs has <num_cpus> bigger than 1")
        exit(1)
else:
    num_lits = 1
    arch_dom = dom.parse(args.arch_xml)
    num_cpus = int(arch_dom.getElementsByTagName("num_cpus")[0].firstChild.nodeValue)
    logging.info("Detected {} CPUs".format(num_cpus))
    if not 'Lit0' in config:
        config['Lit0'] = {}
    config['Lit0']['ami'] = args.ami
    config['Lit0']['archxml'] = args.arch_xml


# Memory Image
mem_image_asm = "{}.{}".format(args.output, MEM_IMAGE_ASM_FILENAME)
for i in range(num_lits):
    ami = config['Lit'+str(i)]['ami']
    logging.debug("Processing '{}'...".format(ami))
    LitUpLib.amiToAsm(ami, mem_image_asm, i)
logging.info("Successfully created " + mem_image_asm)


# Parse SDE debug trace to avoid clock_gettime
if args.real_clock_gettime:
    logging.info("Command-line argument --real-clock-gettime was given. Processing '{}'...".format(args.real_clock_gettime))
    Injections.findTimeStructAddresses(args.real_clock_gettime)


# Parse injection cmd files
inj_asm = "{}.{}".format(args.output, INJECTIONS_ASM_FILENAME)
with open(inj_asm, "w") as injfile:
    injfile.write(";==============================\n")
    injfile.write("; This file was auto-generated\n")
    injfile.write(";==============================\n\n")
    injfile.write("WRITE_SYSCALL_NUMBER{:<21} EQU {}\n".format("", WRITE_SYSCALL_NUMBER))
    injfile.write("CLOCK_GETTIME_SYSCALL_NUMBER{:<21} EQU {}\n".format("", CLOCK_GETTIME_SYSCALL_NUMBER))
    injfile.write("REAL_CLOCK_GETTIME{:<21} EQU {}\n\n".format("", int(args.real_clock_gettime!=None)))
    
    for cpu in range(num_cpus):
        injfile.write("syscall_injections_handler_CPU{}  SEGMENT USE64   ;# at 0{:x}h\n".format(cpu, 0x100000 + (0x40000*cpu)))
        
        # if multi-LIT, each LIT is also CPU num
        lit = 'Lit'+str(cpu) if num_lits > 1 else 'Lit0'
        ami = config[lit]['ami']
        if 'cmd' in config[lit]:
            # if cmd file is defined in the config file and take it from there
            cmd_file = Path(config[lit]['cmd'])
        elif num_lits == 1 and num_cpus > 1:
            # if single-LIT but multi-threaded mode and no cmd in the config-file
            # take the LIT name (AMI basename) with '.<tid>.cmd' extension, e.g. lit.1.cmd for thread 1 (SDE convention)
            cmd_file = cmd_file = (Path(ami).parent / Path(Path(ami).stem + ".{}.cmd".format(cpu))).resolve()
        else:
            # no cmd is given in config file, use the AMI filename + 'cmd' extension
            cmd_file = (Path(ami).parent / Path(Path(ami).stem + ".cmd")).resolve()
        if cmd_file.exists():
            logging.debug("Processing injections file for CPU_{} '{}'...".format(cpu, cmd_file))
            for idx, syscall in enumerate(Injections.parseInjectionsFile(cmd_file)):
                injfile.write("; =====================\n")
                injfile.write("; === System call #{}\n".format(idx))
                injfile.write("; =====================\n")
                for injection in syscall:
                    # skip injections to RIP due to SYSCALLs (which were meant to skip the SYSCALL while we want to do it)
                    if not (injection.register and injection.register.lower() == "rip"):
                        injfile.write(injection.assembly() + "\n\n")
                injfile.write("; Update offset for the next syscall\n")
                injfile.write("lea rax, [rip+11]\n")
                injfile.write("mov [_LINADDR last_inj_lip_CPU{}], rax\n".format(cpu))
                injfile.write("ret\n\n")

        injfile.write("\n; Should never get here\n")
        injfile.write("mov rbx, 0xDEAD\n")
        injfile.write("hlt\n")
        injfile.write("jmp $\n")
        injfile.write("syscall_injections_handler_CPU{}  ENDS\n\n".format(cpu))
logging.info("Successfully created " + inj_asm)


# Parse arch.state.xml
arch_state_asm = "{}.{}".format(args.output, ARCH_STATE_ASM_FILENAME)
for i in range(num_lits):
    archxml = config['Lit'+str(i)]['archxml']
    logging.debug("Processing '{}'...".format(archxml))
    arch_dom    = dom.parse(config['Lit'+str(i)]['archxml'])
    cpu_def     = arch_dom.getElementsByTagName("cpu_definition")[0]
    cpu_state   = arch_dom.getElementsByTagName("cpu_state")[0]
    LitUpLib.archXmlToAsm(archxml, arch_state_asm, num_cpus, cpu_def, cpu_state, i, args.num_instructions)
logging.info("Successfully created " + arch_state_asm)


# Creating template for each CPU
thread_mask = 0
for cpu in range(num_cpus):
    thread_boot_asm         = "{}.cpu_{}_boot.asm".format(args.output, cpu)
    thread_xrstor_amx_asm   = "{}.cpu_{}_xrstore_amx_image.asm".format(args.output, cpu)
    thread_mask             = (thread_mask * 2) + 1;
   
    # Creating per-cpu boot asm file
    thread_boot_template = open(PROG_PATH / "asm" / THREAD_TEMPLATE_FILE)
    with open(thread_boot_asm, "w") as thread_out:
        for line in thread_boot_template:
            line = line.replace("__FTW_IMAGE",              LitUpLib.ftwXrstorValue(cpu))
            line = line.replace("__PMON_COUNT_OS_INSTR",    LitUpLib.pmonCountOsInstrCode(args.pmi_count_os_instr))
            line = line.replace("__SYCALL_INITIALIZATION",  LitUpLib.syscallMsrsInitCode(cpu, args.load_syscall_msrs))
            line = line.replace("__IDT_INITIALIZATION",     LitUpLib.idtInitCode(cpu, args.load_idt))
            line = line.replace("__CET_INITIALIZATION",     LitUpLib.cetInitCode(cpu))
            if not (cpu in LitUpLib.tmul_detected):
                line = line.replace("__AMX_XRSTOR_IMAGE",   "")
            else:
                line = line.replace("__AMX_XRSTOR_IMAGE",   'INCLUDE "{}"\n'.format(thread_xrstor_amx_asm))

            line = line.replace("__CPU_NUM", str(cpu))
            thread_out.write(line)
        thread_out.close()
        thread_boot_template.close()
    logging.info("Successfully created " + thread_boot_asm)

    if cpu in LitUpLib.tmul_detected:
        # Creating per-cpu xrstor AMX image asm file
        thread_xrstor_amx_template = open(PROG_PATH / "asm" / AMX_TEMPLATE_FILE)
        with open(thread_xrstor_amx_asm, "w") as thread_out:
            for line in thread_xrstor_amx_template:
                thread_out.write(line.replace("__CPU_NUM", str(cpu)))

            # if we have TMUL with just 8 tiles, fill the rest with zeros to avoid compilation error
            if not cpu in LitUpLib.tmul16_detected:
                # for tiles 8 to 15
                for i in range(8,16):
                    # for tile lines 0 to 16
                    tileconfig_name = "T{}_TILECONFIG".format(i)
                    thread_out.write("CPU{}_{:<30} EQU 0x0\n".format(cpu, tileconfig_name))
                    for j in range(0,16):
                        tmm_name = "T{}_{:02}".format(i,j)
                        thread_out.write("CPU{}_{:<30} EQU 0x0\n".format(cpu, tmm_name))

            thread_out.close()
            thread_xrstor_amx_template.close()
        logging.info("Successfully created " + thread_xrstor_amx_asm)

logging.debug("Threads mask calculated to {0:b}'b".format(thread_mask))


# Final ASM
output_asm = args.output+'.asm'
boot_origin = open(PROG_PATH / "asm" / BOOT_ASM_FILENAME)
with open(output_asm, "w") as output:
    for line in boot_origin:
        output.write(line.replace("__CPU_MASK", str(thread_mask)))
    boot_origin.close()
    output.write('INCLUDE "{}"\n'.format(mem_image_asm))
    output.write('INCLUDE "{}"\n'.format(arch_state_asm))
    output.write('INCLUDE "{}"\n'.format(inj_asm))
    for i in range(num_cpus):
        thread_state_asm = "{}.cpu_{}_boot.asm".format(args.output, i)
        output.write('INCLUDE "{}"\n'.format(thread_state_asm))
    output.write('\n\n ; END OF FILE\n')
logging.info("Successfully created " + output_asm)


# iASM
if (args.iasm):
    logging.info("Compiling with iASM...")
    FNULL = open(devnull, 'w')
    iasm_command = "{} -no_obj {}".format(args.iasm, output_asm)
    logging.debug(iasm_command)
    try:
        subprocess.check_call(iasm_command, stdout=FNULL, stderr=FNULL, shell=True)
    except subprocess.CalledProcessError:
        logging.error("iASM execution failed! Please check iASM output files for errors")
        exit(1)

    logging.info("Successfully created " + args.output + ".32.obj")
