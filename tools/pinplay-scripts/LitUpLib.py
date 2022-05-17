import logging


##### CONSTANTS #####
DEFAULT_LAST_LIP        = "0x0EFFFFFFFFFFFFFF"  # some non-canonical address
SUPPORTED_REG_GROUPS    = ["fp", "msr", "xmm", "ymm", "zmm", "vpu", "control", "segment", "general", "tmul"]

# Those are MSRs that must be programmed, if they are not available in the arch.xml those will serve as their default value
MANDATORY_MSR_DEFAULTS = {
    'MSR_0x10'  : '0x0',
    'MSR_0x277' : '0x0006060606060606',
    'MSR_0x3a'  : '0x0'
}
#####################


##### MEMBERS #####
ftw             = {} # Dictionary of cpu_num to int value
cet_detected    = {} # Dictionary of cpu_num to boolean
tmul_detected   = {} # Dictionary of cpu_num to boolean
tmul16_detected = {} # Dictionary of cpu_num to boolean
###################


def amiToAsm(ami_filename, mem_image_asm, lit_num):
    write_mode = 'a' if lit_num > 0 else 'w'
    skip_region = False
    
    with open(mem_image_asm, write_mode) as memimage:
        with open(ami_filename, 'r') as ami:
            memimage.write(";===================================================\n")
            memimage.write("; This file was auto-generated from "+ami_filename+"\n")
            memimage.write(";===================================================\n\n")
            memimage.write("memory_segment  SEGMENT USE32   ;# at 00h\n")
            for ami_line in ami:
                if (ami_line.find('/origin') != -1):
                    address = ami_line.split()[1]
                    address = int(address, 16) * 4

                    # in case of merge of LITs, the region at address zero (GDT) can be safely skipped to avoid collision
                    if lit_num > 0 and address == 0:
                        skip_region = True
                        continue
                    else:
                        skip_region = False
                        memimage.write("org " + hex(address) + "\n")

                elif (ami_line.find('/eof') != -1):
                    continue

                elif not skip_region:
                    try:
                        data = int(ami_line, 16)
                        memimage.write("dd " + hex(data) + "\n")
                    except:
                        memimage.write(ami_line + "\n")
            memimage.write("memory_segment  ENDS\n")


def archXmlToAsm(arch_xml_filename, arch_state_asm, num_cpus, cpu_def, cpu_state, lit_num, num_instructions=None):
    write_mode = 'a' if lit_num > 0 else 'w'
    with open(arch_state_asm, write_mode) as archimage:
        archimage.write(";===================================================\n")
        archimage.write("; This file was auto-generated from "+arch_xml_filename+"\n")
        archimage.write(";===================================================\n\n")
        if lit_num == 0:
            archimage.write("NUM_PROCESSORS{:<21} EQU {}\n\n".format("", num_cpus))
        for cpu_element in cpu_def.getElementsByTagName("cpu"):
            # in case of multi-LIT (merging two single threaded LITs) we always have single cpu is its ARCH_XML
            # but the cpu number is the LIT number
            if lit_num > 0:
                cpu_num = lit_num
            else:
                cpu_num = int(cpu_element.getAttribute("num"))
            if (cpu_num >= num_cpus):
                logging.error("Found definition for CPU_{} but <num_cpus> is only {}. Please check your arch.xml consistency.".format(cpu_num, num_cpus))
                exit(1)

            last_ip = DEFAULT_LAST_LIP
            if cpu_element.getElementsByTagName("simulator_specific_data"):
                pinLIT = cpu_element.getElementsByTagName("simulator_specific_data")[0].getElementsByTagName("pinLIT2")[0]
                if pinLIT.getElementsByTagName("baremetal_last_ip"):
                    last_ip = pinLIT.getElementsByTagName("baremetal_last_ip")[0].firstChild.nodeValue
                    logging.info("Last baremetal LIP of CPU_{} is {}".format(cpu_num, last_ip))
                else:
                    logging.info("Last baremetal LIP of CPU_{} was not found, configuring PMI as stopping option".format(cpu_num))

                if not num_instructions:
                    instruction_count = pinLIT.getElementsByTagName("inscount")[0].firstChild.nodeValue
                else:
                    instruction_count = num_instructions

            else:
                if (num_instructions):
                    instruction_count = num_instructions
                else:
                    logging.error('"simulator_specific_data" section not found in the arch.xml. You must provide --num-instructions <n>')
                    exit(1)

            logging.info("Number of instructions of CPU_{} is {}".format(cpu_num, instruction_count))
            archimage.write("CPU{}_{:<30} EQU {}\n".format(cpu_num, "LAST_LIP", last_ip))
            archimage.write("CPU{}_{:<30} EQU {}\n".format(cpu_num, "INST_COUNT", instruction_count))
        for cpu_element in cpu_state.getElementsByTagName("cpu"):
            msrs_found = []
            # in case of multi-LIT (merging two single threaded LITs) we always have single cpu is its ARCH_XML
            # but the cpu number is the LIT number
            if lit_num > 0:
                cpu_num = lit_num
            else:
                cpu_num = int(cpu_element.getAttribute("num"))
            logging.debug("Processing state of CPU_{}".format(cpu_num))
            if (cpu_num >= num_cpus):
                logging.error("Found state for CPU_{} but <num_cpus> is only {}. Please check your arch.xml consistency.".format(cpu_num, num_cpus))
                exit(1)

            for reg_group in cpu_element.childNodes:
                if reg_group.nodeType != reg_group.TEXT_NODE and reg_group.tagName in SUPPORTED_REG_GROUPS:
                    for reg in reg_group.getElementsByTagName("reg"):
                        name = reg.getAttribute("name")
                        value = reg.firstChild.nodeValue
                        if reg_group.tagName == "msr":                          # MSRs have names not addresses
                            addr = reg.getAttribute("addr")
                            msr_name = "MSR_"+addr.lower()
                            msrs_found.append(msr_name)
                            archimage.write("CPU{}_{:<30} EQU {}\n".format(cpu_num, msr_name, value))
                            if (int(addr, 16) == 0xC0000080) and (int(value, 16) & 0x100 == 0):
                                logging.error("32-bit LITs are not yet supported. IA32_EFER (MSR 0xC0000080) value is {}".format(value))
                                exit(1)

                        elif reg_group.tagName == "zmm":                        # ZMMs should be splitted to 4x16B
                            zmm_xmmpart     = "0x{:x}".format( int(value, 16)       & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
                            zmm_ymm_h_part  = "0x{:x}".format((int(value, 16)>>128) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
                            zmm_hi_256_part = "0x{:x}".format((int(value, 16)>>256) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
                            archimage.write("CPU{}_{:<30} EQU {}\n".format(cpu_num, name+"_XMM",    zmm_xmmpart))
                            archimage.write("CPU{}_{:<30} EQU {}\n".format(cpu_num, name+"_YMM_H",  zmm_ymm_h_part))
                            archimage.write("CPU{}_{:<30} EQU {}\n".format(cpu_num, name+"_HI_256", zmm_hi_256_part))

                        elif reg_group.tagName == "tmul":
                            tmul_detected[cpu_num] = True
                            archimage.write("CPU{}_{:<30} EQU {}\n".format(cpu_num, name, value))
                            if name == "T8_TILECONFIG":
                                tmul16_detected[cpu_num] = True

                        elif reg_group.tagName == "segment":                    # segment registers treated specially
                            for attr in reg.getElementsByTagName("attr"):
                                if attr.getAttribute("name") == "base":
                                    base = attr.firstChild.nodeValue
                                if attr.getAttribute("name") == "limit":
                                    limit = attr.firstChild.nodeValue
                            archimage.write("CPU{}_{:<30} EQU {}\n".format(cpu_num, name+"_BASE", base))
                            archimage.write("CPU{}_{:<30} EQU {}\n".format(cpu_num, name+"_LIMIT", limit))
                            selector = reg.getElementsByTagName("selector")
                            if selector:
                                sel = selector[0].firstChild.nodeValue
                                archimage.write("CPU{}_{:<30} EQU {}\n".format(cpu_num, name+"_SELECTOR", sel))

                        else:
                            if name == "TW":
                                ftw[cpu_num] = int(value, 16)
                            if name == "CR4" and ((int(value, 16) & 0x800000) == 1):
                                cet_detected[cpu_num] = True
                            archimage.write("CPU{}_{:<30} EQU {}\n".format(cpu_num, name, value))

            # Make sure all mandatory msrs are added
            for msr in MANDATORY_MSR_DEFAULTS:
                if msr not in msrs_found:
                    archimage.write("CPU{}_{:<30} EQU {}\n".format(cpu_num, msr, MANDATORY_MSR_DEFAULTS[msr]))


def ftwXrstorValue(cpu_num):
    xrstor_ftw = 0;
    for j in range(8):
        STj_TW = (ftw[cpu_num] >> 2*j) & 0x3;
        if STj_TW != 0x3:
            xrstor_ftw |= (1<<j)
    #logging.debug(f"CPU {cpu_num} FTW is 0x{ftw[cpu_num]:x} and corresponding XRSTOR image FTW is 0x{xrstor_ftw:x}")
    return f"0x{xrstor_ftw:x}"
    

def pmonCountOsInstrCode(pmi_count_os_instr=False):
    if not pmi_count_os_instr:
        return ""
    else:
        return "bts eax, 17                     ; Set OS bit to count also ring-0 instructions"


def idtInitCode(cpu_num, load_idt=False):
    if not load_idt:
        return ""
    else:
        return f"""
        ; == Load IDTR ==
        lidt cs:[dword _LINADDR cpu{cpu_num}_idt_ptr]
        jmp short after_lidt_cpu{cpu_num}
        cpu{cpu_num}_idt_ptr:
        dw CPU{cpu_num}_IDTR_LIMIT      ; limit
        dq CPU{cpu_num}_IDTR_BASE       ; base
        after_lidt_cpu{cpu_num}:
        ; Clear the TSS busy bit because LTR will #GP otherwise and will set it when successful
        mov ax, CPU{cpu_num}_TR_SELECTOR
        mov rcx, CPU{cpu_num}_GDTR_BASE
        xor rbx, rbx
        mov bx, ax
        and bx, 0xFFF8                          ; RBX holds entry offset
        btc dword ptr ds:[rcx + rbx + 4], 9     ; bit 9 of the high descriptor is the busy bit 
        ltr ax"""


def cetInitCode(cpu_num):
    if not (cpu_num in cet_detected):
        return ""
    else:
        return f"""
        bt rax, 23      ; CR4[CET] bit
        jnc skip_cet_enabling_cpu_{cpu_num}

        ; == Setup IA32_PL3_SSP MSR ==
        mov ecx, 0x6A7
        mov eax, (CPU{cpu_num}_SSP _AND 0x00000000FFFFFFFF)
        mov edx, (CPU{cpu_num}_SSP _AND 0xFFFFFFFF00000000) _SHR 32
        wrmsr

        ; == Setup IA32_U_CET MSR ==
        mov ecx, 0x6A0
        mov eax, (CPU{cpu_num}_MSR_0x6A0 _AND 0x00000000FFFFFFFF)
        mov edx, (CPU{cpu_num}_MSR_0x6A0 _AND 0xFFFFFFFF00000000) _SHR 32
        wrmsr

        skip_cet_enabling_cpu_{cpu_num}:"""


def syscallMsrsInitCode(cpu_num, load_syscall_msrs=False):
    if not load_syscall_msrs:
        return f"""
        ; == Load LitUp system call handler ==
        mov ecx, 0xc0000082
        mov eax, _LINADDR syscall_handler_CPU{cpu_num}
        xor edx, edx
        wrmsr                       ; IA32_LSTAR
        mov ecx, 0xc0000084
        mov eax, 0x400              ; This bit will clear RFLAGS.DF (string direction) every SYSCALL
        mov edx, 0x0
        wrmsr                       ; IA32_FMASK
        mov ecx, 0xc0000081
        mov eax, (CPU{cpu_num}_MSR_0xC0000081 _AND 0x00000000FFFFFFFF)
        mov edx, (CPU{cpu_num}_MSR_0xC0000081 _AND 0xFFFFFFFF00000000) _SHR 32
        wrmsr                       ; IA32_STAR"""
    else:
        return f"""
        ; == Load system call MSRs ==
        mov ecx, 0xc0000081
        mov eax, (CPU{cpu_num}_MSR_0xC0000081 _AND 0x00000000FFFFFFFF)
        mov edx, (CPU{cpu_num}_MSR_0xC0000081 _AND 0xFFFFFFFF00000000) _SHR 32
        wrmsr                       ; IA32_STAR
        mov ecx, 0xc0000082
        mov eax, (CPU{cpu_num}_MSR_0xC0000082 _AND 0x00000000FFFFFFFF)
        mov edx, (CPU{cpu_num}_MSR_0xC0000082 _AND 0xFFFFFFFF00000000) _SHR 32
        wrmsr                       ; IA32_LSTAR
        mov ecx, 0xc0000083
        mov eax, (CPU{cpu_num}_MSR_0xC0000083 _AND 0x00000000FFFFFFFF)
        mov edx, (CPU{cpu_num}_MSR_0xC0000083 _AND 0xFFFFFFFF00000000) _SHR 32
        wrmsr                       ; IA32_CSTAR
        mov ecx, 0xc0000084
        mov eax, (CPU{cpu_num}_MSR_0xC0000084 _AND 0x00000000FFFFFFFF)
        mov edx, (CPU{cpu_num}_MSR_0xC0000084 _AND 0xFFFFFFFF00000000) _SHR 32
        wrmsr                       ; IA32_FMASK
        mov ecx, 0xc0000100
        mov eax, (CPU{cpu_num}_MSR_0xC0000100 _AND 0x00000000FFFFFFFF)
        mov edx, (CPU{cpu_num}_MSR_0xC0000100 _AND 0xFFFFFFFF00000000) _SHR 32
        wrmsr                       ; IA32_FS_BASE
        mov ecx, 0xc0000101
        mov eax, (CPU{cpu_num}_MSR_0xC0000101 _AND 0x00000000FFFFFFFF)
        mov edx, (CPU{cpu_num}_MSR_0xC0000101 _AND 0xFFFFFFFF00000000) _SHR 32
        wrmsr                       ; IA32_GS_BASE
        mov ecx, 0xc0000102
        mov eax, (CPU{cpu_num}_MSR_0xC0000102 _AND 0x00000000FFFFFFFF)
        mov edx, (CPU{cpu_num}_MSR_0xC0000102 _AND 0xFFFFFFFF00000000) _SHR 32
        wrmsr                       ; IA32_KERNEL_GS_BASE
        mov ecx, 0x174
        mov eax, (CPU{cpu_num}_MSR_0x174 _AND 0x00000000FFFFFFFF)
        mov edx, (CPU{cpu_num}_MSR_0x174 _AND 0xFFFFFFFF00000000) _SHR 32
        wrmsr                       ; IA32_SYSENTER_CS
        mov ecx, 0x175
        mov eax, (CPU{cpu_num}_MSR_0x175 _AND 0x00000000FFFFFFFF)
        mov edx, (CPU{cpu_num}_MSR_0x175 _AND 0xFFFFFFFF00000000) _SHR 32
        wrmsr                       ; IA32_SYSENTER_ESP
        mov ecx, 0x176
        mov eax, (CPU{cpu_num}_MSR_0x176 _AND 0x00000000FFFFFFFF)
        mov edx, (CPU{cpu_num}_MSR_0x176 _AND 0xFFFFFFFF00000000) _SHR 32
        wrmsr                       ; IA32_SYSENTER_EIP"""
