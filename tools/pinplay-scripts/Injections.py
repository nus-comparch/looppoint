import logging
import re
from enum import Enum

_IgnoredAddresses = []

class InjectionType(Enum):
    REGISTER    = 1
    MEMORY      = 2

class Injection:
    def __init__(self, injection_type, value, register=None, address=None, size=None):
        self.injectiontype  = injection_type
        self.value          = value
        self.register       = register
        self.address        = address
        self.size           = size
        
    @staticmethod
    def reservedRegister(reg):
        if reg.lower() in ["rax", "rcx", "rdi", "rsi"]:
            return True
        return False

    @staticmethod
    def registerStackOffset(reg):
        if reg.lower() == "rax":
            return 0x20
        elif reg.lower() == "rcx":
            return 0x18
        elif reg.lower() == "rdi":
            return 0x10
        elif reg.lower() == "rsi":
            return 0x8
        else:
            logging.error("Register {} has no stack offset, it is probably not a reserved register.".format(reg))
            exit(2) 
    
    def inlineMemBytes(self):
        # split the input value by whitechars and hexify
        bytes = [int(c,16) for c in self.value.split()]
        if len(bytes) != self.size:
            logging.error("Size {} of injection to memory {} is not consistent with the amount of injected bytes: {}.".format(self.size, self.address, self.value))
            exit(2) 

        # create a list of lists (each sublist is 8 bytes except the last sublist)
        # so we can compress it using DQ instead of many DBs
        bytes = [bytes[i:i + 8] for i in range(0, len(bytes), 8)]
        code = ""
        for qwordlist in bytes:
            if len(qwordlist) == 8:
                # reverse the list for big-to-little endian when we forge a quad-word
                qword = "".join(['{:02x}'.format(i) for i in qwordlist[::-1]])
                code += "dq 0x{}".format(qword)
            else:
                # here there is no need to reverse as we do it byte-by-byte
                code += "db " + ", ".join(['0x{:02x}'.format(i) for i in qwordlist])
            code += "\n"
        return code

    def assembly(self):
        if self.injectiontype == InjectionType.REGISTER:
            gpr     = re.compile('^r[abcd]x$|^r[ds]i$|^r[bs]p$|^r\d+$')
            segsel  = re.compile('^fs$|^gs$')
            if gpr.match(self.register):
                code = "; Inject {} <- {}\n".format(self.register, self.value)
                if not self.reservedRegister(self.register):
                    code += "mov {}, 0x{}".format(self.register, self.value)
                else:
                    code += "mov rax, 0x{}\n".format(self.value)
                    code += "mov [rsp + {}], rax".format(self.registerStackOffset(self.register))
                return code
            elif segsel.match(self.register):
                code = "; Inject {}.base <- {}\n".format(self.register, self.value)
                code += "mov rax, {}\n".format(self.value)
                code += "wr{}base rax\n".format(self.register)
                return code
            else:
                logging.error("Assembly of injection to register {} is not supported. Currently only GPRs are supported.".format(self.register))
                exit(2)
                
        elif self.injectiontype == InjectionType.MEMORY:
            code = "; Inject {} <- {}\n".format(self.address, self.value)
            code += "mov rcx, {}\n".format(self.size)
            code += "mov rdi, 0x{}\n".format(self.address)
            code += "lea rsi, [rip+5]\n"
            code += "jmp long32 {}\n".format(self.size)
            code += self.inlineMemBytes()
            code += "rep movsb"
            return code
            
        else:
            logging.error("Unsupported injection type while trying to create assembly: {}".format(injectiontype))
            exit(2)


def ignoredAddressInjection(address, size):
    # each ignored address is a 16B struct (assuming Kernel 'timeval' struct is 2 integers)
    for ignoredaddress in _IgnoredAddresses:
        if address >= ignoredaddress and address+size-1 < ignoredaddress+16:
            return True
            
    return False


def parseInjectionsFile(cmdfile):
    # syscalls is a list of lists. For each SYSCALL there will be a list of Injection objects
    syscalls = []
    syscall_injections = []
    with open(cmdfile, 'r') as cmd:
        regex = re.compile('^schedule at (\d+),\s+(.*)\s+// (\w+)')
        syscall_id  = -1
        last_step   = -1
        for cmd_line in cmd:
            cmd_line = cmd_line.strip()
            if not cmd_line:
                continue
            injection_line = regex.match(cmd_line)
            if not injection_line:
                logging.error("Unsupported injection line: {}".format(cmd_line))
                exit(2)
            step            = int(injection_line.group(1))
            injection_string= injection_line.group(2)
            injection       = parseInjection(injection_string)
            instruction     = injection_line.group(3)
            
            if step < last_step:
                logging.error("Injection line has scheduled step smaller than the previous injection line: {}".format(cmd_line))
                exit(2)
                
            if injection.injectiontype != InjectionType.MEMORY and instruction.upper() != "SYSCALL":
                logging.warn("Injections for registers not on SYSCALLs are not yet supported: {}".format(cmd_line))
                continue

            if instruction.upper() != "SYSCALL" and syscall_id == -1:
                logging.error("Injection line before any SYSCALLs are not yet supported: {}".format(cmd_line))
                exit(2)
                
            # If this is a new SYSCALL or injections to previous one
            if instruction.upper() == "SYSCALL" and step != last_step:
                last_step = step
                syscall_id += 1
                if syscall_injections != []:
                    syscalls.append(syscall_injections)
                    syscall_injections = []

            if not (injection.injectiontype == InjectionType.MEMORY and ignoredAddressInjection(int(injection.address,16), injection.size)):
                syscall_injections.append(injection)
                
        if syscall_injections != []:
            syscalls.append(syscall_injections)
    return syscalls


def parseInjection(injection_string):
    reg_regex = re.compile('inject\s+(\w+)\s+with\s+(\w+)')
    sr_regex  = re.compile('reg\s+(\w+)\s+=\s+(.*)')
    mem_regex = re.compile('mem\s+(\w+)\s+(\w+)\s+(\w+)\s+=\s+(.*)')
    
    reg_line = reg_regex.match(injection_string) 
    if (reg_line):
        reg     = reg_line.group(1)
        value   = reg_line.group(2)
        #logging.debug("Found injection to register {} of value {}".format(reg, value))
        return Injection(InjectionType.REGISTER, value, reg)
    
    reg_line = sr_regex.match(injection_string) 
    if (reg_line):
        reg     = reg_line.group(1)
        fullval = reg_line.group(2)
        values  = fullval.strip().split()
        if len(values) != 5:
            logging.error("Unsupported injection to segment register, only 5 dwords injections are supported: {}".format(injection_string))
            exit(2)
        value   = "0x{:x}".format((int(values[0], 16) << 32) | int(values[4], 16))
        #logging.debug("Found injection to segment register {} of value {} (originally: {})".format(reg, value, fullval))
        return Injection(InjectionType.REGISTER, value, reg)

    mem_line = mem_regex.match(injection_string) 
    if (mem_line):
        size        = int(mem_line.group(1),16)
        address_type= mem_line.group(2)
        address     = mem_line.group(3)
        value       = mem_line.group(4)
        if address_type.lower() != "l":
            logging.error("Unsupported injection, only linear (\"l\") memory injections are supported: {}".format(injection_string))
            exit(2)            
        #logging.debug("Found injection to address {} with size {} of value {}".format(address, size, value))
        return Injection(InjectionType.MEMORY, value, None, address, size)
        
    logging.error("Unsupported injection: {}".format(injection))
    exit(2)


def findTimeStructAddresses(sde_trace_file):
    instr_regex     = re.compile(r'.*INS\s\w+\s+\w+\s+(\w+).*\|\s(.*)')
    effects_regex   = re.compile(r'^(\w+) = (\w+)$')
    syscall_found   = False
    
    for line in reverse_readline(sde_trace_file):
        instruction_match = instr_regex.match(line)
        if not instruction_match:
            continue

        mnemonic = instruction_match.group(1).strip()
        effects  = instruction_match.group(2).strip()

        if mnemonic != "syscall" and not syscall_found:
            continue

        if mnemonic == "syscall":
            syscall_found = True
            continue
        
        effects_match = effects_regex.match(effects)
        if effects_match:
            reg = effects_match.group(1).strip()
            val = effects_match.group(2).strip()
            if reg == "rax" and int(val,16) != 228: # not clock_gettime syscall number
                syscall_found = False
                continue
            if reg == "rsi":
                _IgnoredAddresses.append(int(val,16))
                syscall_found = False


def reverse_readline(filename, buf_size=8192):
    """a generator that returns the lines of a file in reverse order"""
    with open(filename, 'r') as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        file_size = remaining_size = fh.tell()
        while remaining_size > 0:
            offset = min(file_size, offset + buf_size)
            fh.seek(file_size - offset)
            buffer = fh.read(min(remaining_size, buf_size))
            remaining_size -= buf_size
            lines = buffer.split('\n')
            # the first line of the buffer is probably not a complete line so
            # we'll save it and append it to the last line of the next buffer
            # we read
            if segment is not None:
                # if the previous chunk starts right from the beginning of line
                # do not concact the segment to the last line of new chunk
                # instead, yield the segment first
                if buffer[-1] != '\n':
                    lines[-1] += segment
                else:
                    yield segment
            segment = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                if lines[index]:
                    yield lines[index]
        # Don't yield None if the file was empty
        if segment is not None:
            yield segment
