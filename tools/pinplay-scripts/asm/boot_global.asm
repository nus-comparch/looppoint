;============================================================================================
; Author:       ilevi1 (itai.levi@intel.com) / bgrinber (boris.grinberg@gmail.com)
; Description:  This file is setting all global definitions for the MP system
;============================================================================================

; === BEGIN GLOBAL CONSTANTS ===
XSAVE_YMM_H_STATE_OFFSET            EQU  0x240  ; CPUID.0xD.0x2.EBX
XSAVE_OPMASK_STATE_OFFSET           EQU  0x440  ; CPUID.0xD.0x5.EBX
XSAVE_ZMM_HI_256_STATE_OFFSET       EQU  0x480  ; CPUID.0xD.0x6.EBX
XSAVE_HI16_ZMM_STATE_OFFSET         EQU  0x680  ; CPUID.0xD.0x7.EBX
XSAVE_XTILECONFIG_STATE_OFFSET      EQU  0xAC0  ; CPUID.0xD.0x11.EBX
XSAVE_XTILEDATA_STATE_OFFSET        EQU  0xB00  ; CPUID.0xD.0x12.EBX
XSAVE_XTILEDATA2_STATE_OFFSET       EQU 0x2B00  ; CPUID.0xD.0x13.EBX
; === END GLOBAL CONSTANTS ===

power_up        SEGMENT USE16   ;# at 0FFFFF000h
    org 0xff0
    jmp boot_start
power_up        ENDS

boot_gdt        SEGMENT USE16   ;# at 0E0800h
    null_boot_gdt_sel:
    dq 0x0000000000000000       ; NULL

    cs_boot_gdt_sel:
    dq 0x00209B0000000000       ; CS

    ss_boot_gdt_sel:
    dq 0x0007970000000000       ; SS

    ds_boot_gdt_sel:
    dq 0x008F93000000FFFF       ; DS
boot_gdt        ENDS

boot_stack      SEGMENT USE16   ;# at 0E1000h
boot_stack      ENDS

pml4            SEGMENT USE32   ;# at 0E2000h
    org 0x0
    dq  (_LINADDR pdpt) _OR (0x23)
pml4            ENDS

pdpt            SEGMENT USE32   ;# at 0E3000h
    org 0x0
    dq 0xE3                     ; linear=physical WB mapping for the lowest 1GB
    org 0x18
    dq 0xC00010FB               ; linear=physical UC mapping for the 4th GB (0xC0000000-0xFFFFFFFF) for APIC_BASE
pdpt            ENDS

boot_idt        SEGMENT USE16   ;# at 0E5000h
    org 0390h
          dw      _LINADDR pmi_int_0x39 _AND 0xFFFF                       ; Lin Offset [15:0]
          dw      (CPU0_GDTR_LIMIT - 0x10) _AND 0xFFF8                    ; Selector is the last in GDT and assuming same limit for all threads
          db      0x0                                                     ; DWORD Count/IST
          db      (0xE _SHL 4) _OR (0xE)                                  ; P=1 DPL=3 0 TYPE=0xE
          dw      (_LINADDR pmi_int_0x39 _AND 0xFFFF0000) _SHR 16         ; Lin Offset [31:16]
          db      (_LINADDR pmi_int_0x39 _AND 0xFF00000000) _SHR 32       ; Lin Offset [39:32]
          db      (_LINADDR pmi_int_0x39 _AND 0xFF0000000000) _SHR 40     ; Lin Offset [47:40]
          db      (_LINADDR pmi_int_0x39 _AND 0xFF000000000000) _SHR 48   ; Lin Offset [55:48]
          db      (_LINADDR pmi_int_0x39 _AND 0xFF00000000000000) _SHR 56 ; Lin Offset [63:56]
          dd      00000000h
boot_idt        ENDS

handlers        SEGMENT USE64   ;# at 0E6000h
    pmi_int_0x39:
        wbinvd
        mov rbx, 0xaced
        hlt
        jmp $                       ; just in case some interrupt wakes us
handlers        ENDS


tss             SEGMENT USE64   ;# at 0E7000h
    dd 00h
    dq _LINADDR boot_stack    ;RSP0
tss             ENDS

barrier         SEGMENT USE32   ;# at 0E0F00h
    thread_id_semaphore : db 0x1
    thread_id           : dd 0x0
    thread_barrier_1    : dd __CPU_MASK
barrier         ENDS

boot            SEGMENT USE16   ;# at 0E0000h
    boot_start:

    ; Try to set semaphore, once semaphore is set read thrad_id, and increment it for the next thread
    ; Thread_id will be set incrementally form BSP, that should be 0
    mov ax, (_LINADDR barrier) _SHR 4
    mov ds, ax

    wait_until_cpu_available:
    mov eax, 0x1
    lock cmpxchg byte ptr ds:[thread_id_semaphore], ah
    jnz wait_until_cpu_available
    mov esi, ds:[thread_id]
    inc ds:[thread_id]
    ; release semaphore
    mov byte ptr ds:[thread_id_semaphore], 1

    ; Check if already enough threads went to boot, halt any additional thread (will not participate in the test)
    cmp esi, NUM_PROCESSORS
    jl cpu_participates_in_test
    mov ebx, 0xACED
    hlt
    cpu_participates_in_test:

    ; == Save Thread ID into IA32_TSC_AUX MSR (address C0000103H) for RDPID instruction
    mov ecx, 0xC0000103
    mov eax, esi
    xor edx, edx
    wrmsr

    ; == Setup boot-time GDT ==
    lgdt cs:[dword OFFSET boot_gdt_ptr]
    jmp short after_boot_lgdt
    boot_gdt_ptr:
    dw 0xFF                     ; limit
    dd _LINADDR boot_gdt        ; base
    after_boot_lgdt:

    lidt cs:[dword OFFSET boot_idt_ptr]
    jmp short after_boot_lidt
    boot_idt_ptr:
    dw 0xFFF                    ; limit
    dd _LINADDR boot_idt        ; base
    after_boot_lidt:

    ; == Setup per thread boot (real mode) stack ==
    ; Allocate 40B per thread, expanding-down
    mov cx, si
    shl cx, 2
    mov ax, (_LINADDR boot_stack) _SHR 4
    add ax, cx
    mov ss, ax
    mov esp, 0x40

    ; == Enter protected + no paging mode ==
    mov eax, 0x50031
    mov cr0, eax
    mov ax, OFFSET ds_boot_gdt_sel
    mov ds, ax

    ; == Enable PAE ==
    mov eax, cr4
    or  eax, 0x20
    mov cr4, eax

    ; == Program CR3 to temp paging structure below 4GB ==
    mov eax, _LINADDR pml4
    mov cr3, eax

    ; == Enable EFER.LME to switch to IA-32e mode) ==
    mov ecx, 0xc0000080
    mov eax, 0x100
    xor edx, edx
    wrmsr

    ; == Setup CR0 to enter 64bit mode ==
    mov eax, 0x80050031
    mov cr0, eax

    ; == APIC Programming ==
    mov ecx, 0x1b
    rdmsr
    or eax, 0x800               ; Set APIC_ENABLE
    wrmsr
    and eax, 0xFFFFF000         ; EAX = APIC base (assuming it is below 32bit)

    ; Set APIC Software Enable in SVR
    mov [eax + 0xf0], 0x100 

    ; Setup APIC LVT PMI to vector 0x39
    mov [eax + 0x340], 0x39

    ; == Wakeup other processors ==
    ; == If not BSP, skip the wakeup of other processors ==
    cmp esi, 0x0
    jne after_sipi_loop

    wait_for_ICR_idle:
    mov ebx, [eax + 0x300]      ; Read ICR[31:0]
    bt eax, 12
    jc wait_for_ICR_idle
    ; write thread physical ID to destination field in the lower ICR
    mov ebx, [eax + 0x310]      ; Read ICR[63:32]
    and ebx, dword 0x00ffffff
    mov edx, 0 
    mov [eax + 0x310], edx      ; Write ICR[63:32]
    mov ebx, [eax + 0x300]      ; Read ICR[31:0]
    and ebx, dword 0xfff3f000   ; Clear the vector, delivery mode, destination mode and shorthand fields
    or  ebx, dword 0x000C0600   ; Write 110 (for startup-IPI) in the delivery mode field, Edge and All Excluding Self
    mov edx, (_LINADDR boot_start _SHR 12)
    or  ebx, edx                ; Write the sipi vector in the vector field
    mov [eax + 0x300], ebx      ; Write ICR[31:0]
    
    after_sipi_loop:

    ; Calculate offset on 64bit code
    mov ecx, esi
    shl ecx, 12
    add ecx, 0xf0000

    ; == Jump to 64-bit mode ==
    pushd 0x10                  ; SS
    pushd 0x0                   ; ESP
    pushd 0x202                 ; EFLAGS
    pushd 0x8                   ; CS
    push ecx                    ; EIP
    iretd
boot            ENDS

clock_gettime   SEGMENT USE64   ;# at 0E8000h
    ; This routine is called from syscall_handler and as such it can corrupt rax,rcx,rdi,rsi because handler backs them up
    
    mov rdi, [rsp + 16]             ; RDI as given to SYSCALL (holds 'const clockid_t which_clock' argument)
    mov rsi, [rsp + 8]              ; RSI as given to SYSCALL (holds 'struct timespec __user * tp' argument)
    
    cmp rdi, 0                      ; We can only support CLOCK_REALTIME (value 0) Kernel clock at the moment
    jne clock_gettime_error
    
    push rbx
    push rdx
    
    mov eax, 0x15                   ; Leaf 0x15 holds: EBX/EAX the ratio between TSC and crystal clock, ECX holds the crystal clock nominal (Hz) frequency
    mov ecx, 0x0
    cpuid
    cmp ebx, 0x0
    je clock_gettime_error          ; We only support processors that have a crystal clock (SKL or GLM and forward)
    cmp ecx, 0x0
    jne cpuid_reports_crystal_hz    ; Some processors do not report their crystal clock frequency

    call get_processor_freq         ; Updates RCX with crystal clock nominal frequency
    cmp ecx, 0x0
    je clock_gettime_error          ; Unsupported processors that might have crystal clock (EBX != 0) but ECX is 0 and even our get_processor_freq doesnt contain its freq

    cpuid_reports_crystal_hz:
    
    ; TSC frequency in Hz = crystal clock nominal frequency * ratio between TSC and crystal clock
    ; So TSC Hz frequency = RCX * EBX/EAX
    ; Time in seconds is TSC / TSC Hz frequency

    ; Since we want to have the time in seconds the decimal leftover in nanoseconds, we will first
    ; calculate the TSC Hz frequency, then read the TSC and multiply it with 10^9 to get the whole time in nano-secs precision
    ; then we will do the division of TSC*10^9 with TSC_freq, such that the result is time in nano-seconds
    ; finally we will divide the result with 10^9, where DIV will return the time in seconds in RAX and the remainder of nanoseconds in RDX
    
    mov rdi, rax
    mov rax, rcx
    mul rbx
    div rdi                         ; RAX = (RCX*RBX/RAX) should be the processor frequency. Remainder in RDX is irrelevant
    mov rdi, rax                    ; Store processor frequency in RDI for a while
    xor rax, rax
    rdtsc                           ; EDX:EAX = TSC
    shl rdx, 32
    or  rax, rdx                    ; RAX = TSC
    mov rdx, 1000000000
    mul rdx                         ; RDX:RAX = TSC * 10^9
    div rdi                         ; RAX = quotient of the time in nano-secs (seconds*10^9), RDX = remainder is irrelevant (less than a nano-second)
    xor rdx, rdx
    mov rdi, 1000000000
    div rdi                         ; RAX = quotient of time (seconds), RDX = remainder of time (nano-seconds)
    mov [rsi],   rax
    mov [rsi+8], rdx
    
    pop rdx
    pop rbx
    ret
    
    clock_gettime_error:
    mov rbx, 0xDEAD
    hlt
    jmp $
    
    

    ; Below routine is returning processor crystal clock nominal frequency (Hz) into RCX
    ; The crystal clock logic was taken from Linux Kernel turbostat.c
    ; The Intel processor models were taken from Linux Kernel intel-family.h
    ;
    ;   __cpuid(1, fms, ebx, ecx, edx);
    ;   family = (fms >> 8) & 0xf;
    ;   model = (fms >> 4) & 0xf;
    ;   stepping = fms & 0xf;
    ;   if (family == 0xf)
    ;       family += (fms >> 20) & 0xff;
    ;   if (family >= 6)
    ;       model += ((fms >> 16) & 0xf) << 4;
    ;   ...
    ;   ...
    ;   
    ;   switch(model) {
    ;   case INTEL_FAM6_SKYLAKE_MOBILE:     /* SKL */       0x4E
    ;   case INTEL_FAM6_SKYLAKE_DESKTOP:	/* SKL */       0x5E
    ;   case INTEL_FAM6_KABYLAKE_MOBILE:	/* KBL */       0x55
    ;   case INTEL_FAM6_KABYLAKE_DESKTOP:	/* KBL */       0x9E
    ;       crystal_hz = 24000000;  /* 24.0 MHz */
    ;       break;
    ;   case INTEL_FAM6_ATOM_GOLDMONT_X:    /* DNV */       0x5F
    ;       crystal_hz = 25000000;  /* 25.0 MHz */      
    ;       break;
    ;   case INTEL_FAM6_ATOM_GOLDMONT:      /* BXT */       0x5C
    ;   case INTEL_FAM6_ATOM_GOLDMONT_PLUS:                 0x7A
    ;       crystal_hz = 19200000;  /* 19.2 MHz */
    ;       break;
    ;   default:
    ;       crystal_hz = 0;

    get_processor_freq:
        push rax
        push rbx
        push rdx
    
        mov eax, 0x1                
        cpuid                           ; Leaf 0x1 return processor FMS (family/model/stepping) into EAX
        mov ebx, eax
        shr ebx, 8
        and ebx, 0xF                    ; EBX = FMS[11:8] (family)
        cmp ebx, 0xF
        jne not_family_0xF
            mov ecx, eax
            shr ecx, 20
            and ecx, 0xFF
            add ebx, ecx                ; if family==0xF: family += extended_family (FMS[27:20])
        not_family_0xF:
        mov edx, eax
        shr edx, 4
        and edx, 0xF                    ; EDX = FMS[7:4] (model)
        cmp ebx, 0x5
        jbe not_family_bigger_0x5
            mov ecx, eax
            shr ecx, 16
            and ecx, 0xF
            shl ecx, 4
            add edx, ecx                ; if family>5: model is concatinated to extended model (FMS[19:16])
        not_family_bigger_0x5:
        
        cmp edx, 0x4E
        je crystal_hz_24
        cmp edx, 0x5E
        je crystal_hz_24
        cmp edx, 0x55
        je crystal_hz_24
        cmp edx, 0x9E
        je crystal_hz_24
        
        cmp edx, 0x5F
        je crystal_hz_25
        
        cmp edx, 0x5C
        je crystal_hz_19_2
        cmp edx, 0x7A
        je crystal_hz_19_2

        mov rcx, 0
        pop rdx
        pop rbx
        pop rax
        ret
        
        crystal_hz_24:
            mov rcx, 24000000
            pop rdx
            pop rbx
            pop rax
            ret
        crystal_hz_25:
            mov rcx, 25000000
            pop rdx
            pop rbx
            pop rax
            ret
        crystal_hz_19_2:
            mov rcx, 19200000
            pop rdx
            pop rbx
            pop rax
            ret
        
clock_gettime   ENDS
