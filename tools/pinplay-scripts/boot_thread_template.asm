xrstor_image_CPU__CPU_NUM    SEGMENT USE16   ;# at 0__CPU_NUM2000h
    dw CPU__CPU_NUM_CW                                  ; FCW
    dw CPU__CPU_NUM_SW                                  ; FSW
    db __FTW_IMAGE                                      ; FTW
    db 0x0                                              ; Reserved
    dw CPU__CPU_NUM_OPCODE                              ; FOP
    dd CPU__CPU_NUM_FIP                                 ; FIP
    dd CPU__CPU_NUM_FCS                                 ; FCS
    dd CPU__CPU_NUM_DATAOP                              ; FDP
    dd CPU__CPU_NUM_FDS                                 ; FDS
    dd CPU__CPU_NUM_MXCSR                               ; MXCSR
    dd 0xffff                                           ; MXCSR Mask
    do CPU__CPU_NUM_FR0                                 ; ST0
    do CPU__CPU_NUM_FR1                                 ; ST1
    do CPU__CPU_NUM_FR2                                 ; ST2
    do CPU__CPU_NUM_FR3                                 ; ST3
    do CPU__CPU_NUM_FR4                                 ; ST4
    do CPU__CPU_NUM_FR5                                 ; ST5
    do CPU__CPU_NUM_FR6                                 ; ST6
    do CPU__CPU_NUM_FR7                                 ; ST7
    do CPU__CPU_NUM_ZMM0_XMM                            ; XMM0
    do CPU__CPU_NUM_ZMM1_XMM                            ; XMM1
    do CPU__CPU_NUM_ZMM2_XMM                            ; XMM2
    do CPU__CPU_NUM_ZMM3_XMM                            ; XMM3
    do CPU__CPU_NUM_ZMM4_XMM                            ; XMM4
    do CPU__CPU_NUM_ZMM5_XMM                            ; XMM5
    do CPU__CPU_NUM_ZMM6_XMM                            ; XMM6
    do CPU__CPU_NUM_ZMM7_XMM                            ; XMM7
    do CPU__CPU_NUM_ZMM8_XMM                            ; XMM8
    do CPU__CPU_NUM_ZMM9_XMM                            ; XMM9
    do CPU__CPU_NUM_ZMM10_XMM                           ; XMM10
    do CPU__CPU_NUM_ZMM11_XMM                           ; XMM11
    do CPU__CPU_NUM_ZMM12_XMM                           ; XMM12
    do CPU__CPU_NUM_ZMM13_XMM                           ; XMM13
    do CPU__CPU_NUM_ZMM14_XMM                           ; XMM14
    do CPU__CPU_NUM_ZMM15_XMM                           ; XMM15
    db 48 dup (0x0)                                     ; Reserved area - Bytes 463:416
    db 48 dup (0x0)                                     ; Unused area   - Bytes 511:464
    xrstor_image_header_CPU__CPU_NUM:
    dq 0xFFFFFFFFFFFFFFFF                               ; Header (XSTATE_BV)
    dq 0x0000000000000000                               ; Header (XCOMP_BV)
    db 48 dup (0x0)                                     ; Header (Reserved) - Bytes 63:16 of the header

    org XSAVE_YMM_H_STATE_OFFSET
    do CPU__CPU_NUM_ZMM0_YMM_H                          ; YMM0_H
    do CPU__CPU_NUM_ZMM1_YMM_H                          ; YMM1_H
    do CPU__CPU_NUM_ZMM2_YMM_H                          ; YMM2_H
    do CPU__CPU_NUM_ZMM3_YMM_H                          ; YMM3_H
    do CPU__CPU_NUM_ZMM4_YMM_H                          ; YMM4_H
    do CPU__CPU_NUM_ZMM5_YMM_H                          ; YMM5_H
    do CPU__CPU_NUM_ZMM6_YMM_H                          ; YMM6_H
    do CPU__CPU_NUM_ZMM7_YMM_H                          ; YMM7_H
    do CPU__CPU_NUM_ZMM8_YMM_H                          ; YMM8_H
    do CPU__CPU_NUM_ZMM9_YMM_H                          ; YMM9_H
    do CPU__CPU_NUM_ZMM10_YMM_H                         ; YMM10_H
    do CPU__CPU_NUM_ZMM11_YMM_H                         ; YMM11_H
    do CPU__CPU_NUM_ZMM12_YMM_H                         ; YMM12_H
    do CPU__CPU_NUM_ZMM13_YMM_H                         ; YMM13_H
    do CPU__CPU_NUM_ZMM14_YMM_H                         ; YMM14_H
    do CPU__CPU_NUM_ZMM15_YMM_H                         ; YMM15_H

    org XSAVE_OPMASK_STATE_OFFSET
    dq CPU__CPU_NUM_K0                                  ; K0
    dq CPU__CPU_NUM_K1                                  ; K1
    dq CPU__CPU_NUM_K2                                  ; K2
    dq CPU__CPU_NUM_K3                                  ; K3
    dq CPU__CPU_NUM_K4                                  ; K4
    dq CPU__CPU_NUM_K5                                  ; K5
    dq CPU__CPU_NUM_K6                                  ; K6
    dq CPU__CPU_NUM_K7                                  ; K7

    org XSAVE_ZMM_HI_256_STATE_OFFSET
    dy CPU__CPU_NUM_ZMM0_HI_256                         ; ZMM0_HI_256
    dy CPU__CPU_NUM_ZMM1_HI_256                         ; ZMM1_HI_256
    dy CPU__CPU_NUM_ZMM2_HI_256                         ; ZMM2_HI_256
    dy CPU__CPU_NUM_ZMM3_HI_256                         ; ZMM3_HI_256
    dy CPU__CPU_NUM_ZMM4_HI_256                         ; ZMM4_HI_256
    dy CPU__CPU_NUM_ZMM5_HI_256                         ; ZMM5_HI_256
    dy CPU__CPU_NUM_ZMM6_HI_256                         ; ZMM6_HI_256
    dy CPU__CPU_NUM_ZMM7_HI_256                         ; ZMM7_HI_256
    dy CPU__CPU_NUM_ZMM8_HI_256                         ; ZMM8_HI_256
    dy CPU__CPU_NUM_ZMM9_HI_256                         ; ZMM9_HI_256
    dy CPU__CPU_NUM_ZMM10_HI_256                        ; ZMM10_HI_256
    dy CPU__CPU_NUM_ZMM11_HI_256                        ; ZMM11_HI_256
    dy CPU__CPU_NUM_ZMM12_HI_256                        ; ZMM12_HI_256
    dy CPU__CPU_NUM_ZMM13_HI_256                        ; ZMM13_HI_256
    dy CPU__CPU_NUM_ZMM14_HI_256                        ; ZMM14_HI_256
    dy CPU__CPU_NUM_ZMM15_HI_256                        ; ZMM15_HI_256

    org XSAVE_HI16_ZMM_STATE_OFFSET
    do CPU__CPU_NUM_ZMM16_XMM                           ; ZMM16
    do CPU__CPU_NUM_ZMM16_YMM_H
    dy CPU__CPU_NUM_ZMM16_HI_256
    do CPU__CPU_NUM_ZMM17_XMM                           ; ZMM17
    do CPU__CPU_NUM_ZMM17_YMM_H
    dy CPU__CPU_NUM_ZMM17_HI_256
    do CPU__CPU_NUM_ZMM18_XMM                           ; ZMM18
    do CPU__CPU_NUM_ZMM18_YMM_H
    dy CPU__CPU_NUM_ZMM18_HI_256
    do CPU__CPU_NUM_ZMM19_XMM                           ; ZMM19
    do CPU__CPU_NUM_ZMM19_YMM_H
    dy CPU__CPU_NUM_ZMM19_HI_256
    do CPU__CPU_NUM_ZMM20_XMM                           ; ZMM20
    do CPU__CPU_NUM_ZMM20_YMM_H
    dy CPU__CPU_NUM_ZMM20_HI_256
    do CPU__CPU_NUM_ZMM21_XMM                           ; ZMM21
    do CPU__CPU_NUM_ZMM21_YMM_H
    dy CPU__CPU_NUM_ZMM21_HI_256
    do CPU__CPU_NUM_ZMM22_XMM                           ; ZMM22
    do CPU__CPU_NUM_ZMM22_YMM_H
    dy CPU__CPU_NUM_ZMM22_HI_256
    do CPU__CPU_NUM_ZMM23_XMM                           ; ZMM23
    do CPU__CPU_NUM_ZMM23_YMM_H
    dy CPU__CPU_NUM_ZMM23_HI_256
    do CPU__CPU_NUM_ZMM24_XMM                           ; ZMM24
    do CPU__CPU_NUM_ZMM24_YMM_H
    dy CPU__CPU_NUM_ZMM24_HI_256
    do CPU__CPU_NUM_ZMM25_XMM                           ; ZMM25
    do CPU__CPU_NUM_ZMM25_YMM_H
    dy CPU__CPU_NUM_ZMM25_HI_256
    do CPU__CPU_NUM_ZMM26_XMM                           ; ZMM26
    do CPU__CPU_NUM_ZMM26_YMM_H
    dy CPU__CPU_NUM_ZMM26_HI_256
    do CPU__CPU_NUM_ZMM27_XMM                           ; ZMM27
    do CPU__CPU_NUM_ZMM27_YMM_H
    dy CPU__CPU_NUM_ZMM27_HI_256
    do CPU__CPU_NUM_ZMM28_XMM                           ; ZMM28
    do CPU__CPU_NUM_ZMM28_YMM_H
    dy CPU__CPU_NUM_ZMM28_HI_256
    do CPU__CPU_NUM_ZMM29_XMM                           ; ZMM29
    do CPU__CPU_NUM_ZMM29_YMM_H
    dy CPU__CPU_NUM_ZMM29_HI_256
    do CPU__CPU_NUM_ZMM30_XMM                           ; ZMM30
    do CPU__CPU_NUM_ZMM30_YMM_H
    dy CPU__CPU_NUM_ZMM30_HI_256
    do CPU__CPU_NUM_ZMM31_XMM                           ; ZMM31
    do CPU__CPU_NUM_ZMM31_YMM_H
    dy CPU__CPU_NUM_ZMM31_HI_256
    
    __AMX_XRSTOR_IMAGE

    xrstor_image_CPU__CPU_NUM    ENDS


boot64_CPU__CPU_NUM          SEGMENT USE64   ;# at 0F__CPU_NUM000h
    ; == Reset Stack for Long mode -> reusing same stack used for real mode ==
    ; Allocate 40B per thread, expanding-down
    mov rcx, rsi
    shl rcx, 6
    mov rsp, _LINADDR boot_stack
    add rsp, rcx
    add rsp, 0x40

    ; == Setup IA32_MTRR_DEF_TYPE ==
    mov ecx, 0x2ff
    mov eax, 0x806
    xor edx, edx
    wrmsr

    ; == Setup IA32_FEATURE_CONTROL ==
    mov ecx, 0x3a
    rdmsr
    test ax, 0x1                ; test if lock bit is on
    jnz boot_feature_control_already_locked_CPU__CPU_NUM
    mov eax, (CPU__CPU_NUM_MSR_0x3A _AND 0x00000000FFFFFFFF)
    mov edx, (CPU__CPU_NUM_MSR_0x3A _AND 0xFFFFFFFF00000000) _SHR 32
    or eax, 0x1                 ; lock bit
    wrmsr
    boot_feature_control_already_locked_CPU__CPU_NUM:

    ; == Setup IA32_PAT ==
    mov ecx, 0x277
    mov eax, (CPU__CPU_NUM_MSR_0x277 _AND 0x00000000FFFFFFFF)
    mov edx, (CPU__CPU_NUM_MSR_0x277 _AND 0xFFFFFFFF00000000) _SHR 32
    wrmsr

    ; == Setup IA32_MISC_ENABLE ==
    mov ecx, 0x1a0
    mov eax, (CPU__CPU_NUM_MSR_0x1A0 _AND 0x00000000FFFFFFFF)
    mov edx, (CPU__CPU_NUM_MSR_0x1A0 _AND 0xFFFFFFFF00000000) _SHR 32
    ; Before programming IA32_MISC_ENABLE, clear bit 38 - this bit is special, if it is st it is merely an indication
    ; of Turbo support and writing 1 to it will actually disable it which is not desired
    btr edx, 6
    wrmsr

    ; == Reset EFER.LME to CPU intended value ==
    mov ecx, 0xc0000080
    mov eax, (CPU__CPU_NUM_MSR_0xC0000080 _AND 0x00000000FFFFFFFF)
    mov edx, (CPU__CPU_NUM_MSR_0xC0000080 _AND 0xFFFFFFFF00000000) _SHR 32
    wrmsr

    ; == Setup PMONS for instruction count if last LIP is bogus (wasn't found by SDE) ==
    mov rcx, CPU__CPU_NUM_LAST_LIP
    mov rax, 0x0EFFFFFFFFFFFFFF
    cmp rcx, rax
    jne skip_pmon_set_cpu___CPU_NUM

    mov ecx, 0x186      ; IA32_PERFEVTSEL0
    mov eax, 0x5100C0   ; count Instruction Retired, USR , INT, EN
    __PMON_COUNT_OS_INSTR
    mov edx, 0x0
    wrmsr

    mov ecx, 0xC1       ; counter to oveflow
    mov eax, 0xffffffff
    sub eax, CPU__CPU_NUM_INST_COUNT
    mov edx, 0xffff
    wrmsr

    mov ecx, 0x38F ; IA32_PERF_GLOBAL_CTRL
    mov eax, 1     ; Enable IA32_PERFEVTSEL0
    mov edx, 0
    wrmsr

    mov ecx, 0x3F1 ; IA32_PEBS_ENABLE 
    mov eax, 1     ; Enable IA32_PERFEVTSEL0
    mov edx, 0
    wrmsr

    ; = setup DS area for PEBS EVENTS
    mov ecx, 0x600 ; IA32_DS_AREA
    mov eax, _LINADDR pebs_ds_area_CPU__CPU_NUM
    mov edx, 0
    wrmsr

    skip_pmon_set_cpu___CPU_NUM:

    ; == Reset CR0 to CPU intended value ==
    mov rax, CPU__CPU_NUM_CR0
    mov cr0, rax

    ; == Setup CR3 ==
    mov rax, CPU__CPU_NUM_CR3
    mov cr3, rax

    ; == Setup CR4 ==
    mov rax, CPU__CPU_NUM_CR4
    bt rax, 17
    jnc cr4_pcide_not_set_CPU__CPU_NUM
    ; Must clear CR3[11:0] enabling CR4.PCIDE, then reload it
    mov rbx, cr3
    and rbx, (_NOT 0xFFF)
    mov cr3, rbx
    mov cr4, rax
    mov rbx, CPU__CPU_NUM_CR3
    mov cr3, rbx
    cr4_pcide_not_set_CPU__CPU_NUM:
    mov cr4, rax
    
    __CET_INITIALIZATION

    ; == Setup XCR0 ==
    xor rcx, rcx
    mov rax, CPU__CPU_NUM_XCR0
    xor rdx, rdx
    xsetbv
    mov ds:[_LINADDR xrstor_image_header_CPU__CPU_NUM], rax

    ; == HACK1: Updating GDT CS entry to be marked as CODE with correct DPL (SDE and other tracers sometime configure the descriptor incorrectly) ==
    mov rcx, CPU__CPU_NUM_GDTR_BASE
    mov rbx, CPU__CPU_NUM_CS_SELECTOR
    mov rax, rbx
    and bx, 0xFFF8                      ; RBX holds entry offset
    and ax, 0x3                         ; AX holds CS.CPL to be written as DPL
    shl ax, 5
    or  ax, 0x9B                      ; 0x9B for bits 47:40 of the upper descriptor (code segment) merged with DPL
    mov byte ptr ds:[rcx + rbx + 5], al

    ; == HACK2: Updating GDT to include handlers segment ==
    mov rax, 0x00209b0E60000FFF
    mov rcx, CPU__CPU_NUM_GDTR_BASE
    mov rbx, CPU__CPU_NUM_GDTR_LIMIT - 0x10
    and bx, 0xFFF8
    mov ds:[rcx + rbx], rax

    ; == HACK3: Updating GDT to include TSS segment ==
    mov rax, 0x000e90E7000016b
    mov rcx, CPU__CPU_NUM_GDTR_BASE
    mov rbx, CPU__CPU_NUM_GDTR_LIMIT - 0x10
    sub rbx, (__CPU_NUM _SHL 4) + 0x10  ; GDT holds handlers descriptor on last descriptor and then TSS descriptor per thread (going backwards)
    and bx, 0xFFF8
    mov ds:[rcx + rbx], rax
    mov ds:[rcx + rbx + 0x8], qword 0x0 ; clear the next entry since TSS would take 2 entries

    ; == Setup GDT ==
    lgdt cs:[dword _LINADDR CPU__CPU_NUM_GDT_PTR]
    jmp short after_cpu0_lgdt_CPU__CPU_NUM
    CPU__CPU_NUM_GDT_PTR:
    dw CPU__CPU_NUM_GDTR_LIMIT
    dq CPU__CPU_NUM_GDTR_BASE
    after_cpu0_lgdt_CPU__CPU_NUM:

    ; == Load active TSS ==
    mov rax, CPU__CPU_NUM_GDTR_LIMIT - 0x10
    sub rax, (__CPU_NUM _SHL 4) + 0x10
    and ax, 0xFFF8
    ltr ax

    ; == XRSTOR state ==
    vzeroall
    fninit
    mov eax, 0xFFFFFFFF
    mov edx, 0x0
    xrstor ds:[_LINADDR xrstor_image_CPU__CPU_NUM]

    __SYCALL_INITIALIZATION

    __IDT_INITIALIZATION

    ; == Load segment selectors ==
    mov ax, CPU__CPU_NUM_DS_SELECTOR
    mov ds, ax
    mov ax, CPU__CPU_NUM_ES_SELECTOR
    mov es, ax
    mov ax, CPU__CPU_NUM_FS_SELECTOR
    mov fs, ax
    mov ax, CPU__CPU_NUM_GS_SELECTOR
    mov gs, ax
    
    mov rax, cr4
    bts rax, 16                         ; Set CR4.FSGSBASE to use WRFSBASE/WRGSBASE instructions
    mov cr4, rax
    mov rax, CPU__CPU_NUM_FS_BASE
    wrfsbase rax
    mov rax, CPU__CPU_NUM_GS_BASE
    wrgsbase rax

    ; == Load TSC MSR if supplied ==
    mov rax, CPU__CPU_NUM_MSR_0x10
    test rax, rax
    jz skip_wrmsr_tsc_cpu___CPU_NUM
    mov ecx, 0x10               ; IA32_TIME_STAMP_COUNTER
    mov eax, (CPU__CPU_NUM_MSR_0x10 _AND 0x00000000FFFFFFFF)
    mov edx, (CPU__CPU_NUM_MSR_0x10 _AND 0xFFFFFFFF00000000) _SHR 32
    wrmsr
    skip_wrmsr_tsc_cpu___CPU_NUM:

    ; == Load GPRs (except RAX) ==
    mov rbx, CPU__CPU_NUM_RBX
    mov rcx, CPU__CPU_NUM_RCX
    mov rdx, CPU__CPU_NUM_RDX
    mov rsi, CPU__CPU_NUM_RSI
    mov rdi, CPU__CPU_NUM_RDI
    mov r8,  CPU__CPU_NUM_R8
    mov r9,  CPU__CPU_NUM_R9
    mov r10, CPU__CPU_NUM_R10
    mov r11, CPU__CPU_NUM_R11
    mov r12, CPU__CPU_NUM_R12
    mov r13, CPU__CPU_NUM_R13
    mov r14, CPU__CPU_NUM_R14
    mov r15, CPU__CPU_NUM_R15

    ; == Start test barrier ==
    start_test_barrier_thread__CPU_NUM:
    lock and dword ptr ds:[_LINADDR thread_barrier_1], _NOT  (dword 1 _SHL __CPU_NUM)
    cmp dword ptr ds:[_LINADDR thread_barrier_1], dword 0x0
    pause
    jnz long32 start_test_barrier_thread__CPU_NUM

    ; == Jump to user code ==
    mov rbp, CPU__CPU_NUM_RBP
    push CPU__CPU_NUM_SS_SELECTOR       ; SS
    mov rax, CPU__CPU_NUM_RSP
    push rax                            ; RSP
    mov rax, CPU__CPU_NUM_RFLAGS
    bts rax, 9                          ; Set RFLAGS.IF (for PMIs)
    push rax                            ; RFLAGS
    push CPU__CPU_NUM_CS_SELECTOR       ; CS
    mov rax, CPU__CPU_NUM_RIP
    push rax                            ; RIP
    mov rax, CPU__CPU_NUM_RAX
    iretq

    ; == Should never get here ==
    mov rbx, 0xDEAD
    hlt                         ; could be that we get here in ring-3, so we will shutdown
    jmp $                       ; just in case some interrupt wakes us
boot64_CPU__CPU_NUM          ENDS

pebs_ds_area_CPU__CPU_NUM    SEGMENT USE16   ;# at 0E4__CPU_NUM00h
    ; PEBS DS area is created such that the index address will exceed the threshold address after just one PEBS
    ; counter overflow will cause PEBS dump, but since the exceed the threshold we will get PMI and stop the thread
    org 0x20
    pebs_base_addr_CPU__CPU_NUM      : dq _LINADDR pebs_ds_area_CPU__CPU_NUM + 0x50
    pebs_index_addr_CPU__CPU_NUM     : dq _LINADDR pebs_ds_area_CPU__CPU_NUM + 0x50
    pebs_abs_max_addr_CPU__CPU_NUM   : dq _LINADDR pebs_ds_area_CPU__CPU_NUM + 0xFF
    pebs_threshold_addr_CPU__CPU_NUM : dq _LINADDR pebs_ds_area_CPU__CPU_NUM + 0x58
pebs_ds_area_CPU__CPU_NUM    ENDS

syscall_handler_CPU__CPU_NUM    SEGMENT USE64   ;# at 0E9__CPU_NUM00h
    push rax
    push rcx
    push rdi
    push rsi

    ; RCX holds the LIP of instruction following the SYSCALL, if it is equal to last LIP + 2B (SYSCALL opcode size) we finished
    ; Otherwise, we should do any side effect injection this SYSCALL might have
    mov rdi, CPU__CPU_NUM_LAST_LIP + 2
    cmp rcx, rdi
    je finished_successfully__CPU_NUM
    
    ; =========================================================================
    ; Specialized code for the case '--real-clock-gettime' was given in cmdline
    ; =========================================================================
    mov dil, REAL_CLOCK_GETTIME
    cmp dil, 1
    jne not_real_clock_gettime__CPU_NUM

    ; This check will succeed if this is a write() system call and '--real-clock-gettime' was given in cmdline
    ; in this case, prints might be dependent on the time and therefore bigger/smaller buffers might be sent as input
    ; and we must return the same number (return value is number of bytes written) to avoid the calling Linux Kernel (still user code part)
    ; from doing calling again to the write() system call and causing the number of syscalls to be out-of-sync from recording
    cmp eax, WRITE_SYSCALL_NUMBER
    jne not_write_syscall__CPU_NUM
    mov [_LINADDR write_count__CPU_NUM], edx    ; EDX holds third parameter (size_t count) to the write system call
    not_write_syscall__CPU_NUM:

    ; This check will succeed if this is a clock_gettime() system call and 
    ; in this case we would like to jump to specialized code for returning real time
    cmp eax, CLOCK_GETTIME_SYSCALL_NUMBER
    jne not_real_clock_gettime__CPU_NUM
    mov rax, _LINADDR clock_gettime
    call rax
    not_real_clock_gettime__CPU_NUM:

    ; ===========================================
    ; Main entry point for system call injections
    ; ===========================================
    mov rax, [_LINADDR last_inj_lip_CPU__CPU_NUM]
    call rax
    
    ; This check will succeed if this is a write() system call and '--real-clock-gettime' was given in cmdline
    ; in this case, the above code stores aside the syscall EDX input which needs to be written to RAX as return value
    cmp dword ptr [_LINADDR write_count__CPU_NUM], 0xFFFFFFFF
    je return_from_syscall__CPU_NUM
    mov eax, [_LINADDR write_count__CPU_NUM]
    mov [rsp + 24], eax
    return_from_syscall__CPU_NUM:

    pop rsi
    pop rdi
    pop rcx
    pop rax
    rex_w1 sysret
    
    ; If we got here, we came from the last LIP in the LIT and we can finish succesfully
    finished_successfully__CPU_NUM:
    wbinvd
    mov rbx, 0xACED
    hlt
    jmp $                       ; just in case some interrupt wakes us

    last_inj_lip_CPU__CPU_NUM:
    dq _LINADDR syscall_injections_handler_CPU__CPU_NUM

    write_count__CPU_NUM:
    dd 0xFFFFFFFF
    
syscall_handler_CPU__CPU_NUM    ENDS
