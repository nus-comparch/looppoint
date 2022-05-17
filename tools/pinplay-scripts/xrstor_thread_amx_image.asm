    org XSAVE_XTILECONFIG_STATE_OFFSET
    db CPU__CPU_NUM_T0_TILECONFIG _SHR 56               ; TILECONFIG[palette_id]
    db (CPU__CPU_NUM_T0_TILECONFIG _SHR 48) _AND 0xFF   ; TILECONFIG[start_row]
    db 14 dup (0x0)                                     ; TILECONFIG[reserved MBZ]
    dw (CPU__CPU_NUM_T0_TILECONFIG _SHR 8) _AND 0xFFFF  ; TILECONFIG[tile0.colsb]
    dw (CPU__CPU_NUM_T1_TILECONFIG _SHR 8) _AND 0xFFFF  ; TILECONFIG[tile1.colsb]
    dw (CPU__CPU_NUM_T2_TILECONFIG _SHR 8) _AND 0xFFFF  ; TILECONFIG[tile2.colsb]
    dw (CPU__CPU_NUM_T3_TILECONFIG _SHR 8) _AND 0xFFFF  ; TILECONFIG[tile3.colsb]
    dw (CPU__CPU_NUM_T4_TILECONFIG _SHR 8) _AND 0xFFFF  ; TILECONFIG[tile4.colsb]
    dw (CPU__CPU_NUM_T5_TILECONFIG _SHR 8) _AND 0xFFFF  ; TILECONFIG[tile5.colsb]
    dw (CPU__CPU_NUM_T6_TILECONFIG _SHR 8) _AND 0xFFFF  ; TILECONFIG[tile6.colsb]
    dw (CPU__CPU_NUM_T7_TILECONFIG _SHR 8) _AND 0xFFFF  ; TILECONFIG[tile7.colsb]
    dw (CPU__CPU_NUM_T8_TILECONFIG _SHR 8) _AND 0xFFFF  ; TILECONFIG[tile8.colsb]
    dw (CPU__CPU_NUM_T9_TILECONFIG _SHR 8) _AND 0xFFFF  ; TILECONFIG[tile9.colsb]
    dw (CPU__CPU_NUM_T10_TILECONFIG _SHR 8) _AND 0xFFFF ; TILECONFIG[tile10.colsb]
    dw (CPU__CPU_NUM_T11_TILECONFIG _SHR 8) _AND 0xFFFF ; TILECONFIG[tile11.colsb]
    dw (CPU__CPU_NUM_T12_TILECONFIG _SHR 8) _AND 0xFFFF ; TILECONFIG[tile12.colsb]
    dw (CPU__CPU_NUM_T13_TILECONFIG _SHR 8) _AND 0xFFFF ; TILECONFIG[tile13.colsb]
    dw (CPU__CPU_NUM_T14_TILECONFIG _SHR 8) _AND 0xFFFF ; TILECONFIG[tile14.colsb]
    dw (CPU__CPU_NUM_T15_TILECONFIG _SHR 8) _AND 0xFFFF ; TILECONFIG[tile15.colsb]
    db CPU__CPU_NUM_T0_TILECONFIG _AND 0xFF             ; TILECONFIG[tile0.rows]
    db CPU__CPU_NUM_T1_TILECONFIG _AND 0xFF             ; TILECONFIG[tile1.rows]
    db CPU__CPU_NUM_T2_TILECONFIG _AND 0xFF             ; TILECONFIG[tile2.rows]
    db CPU__CPU_NUM_T3_TILECONFIG _AND 0xFF             ; TILECONFIG[tile3.rows]
    db CPU__CPU_NUM_T4_TILECONFIG _AND 0xFF             ; TILECONFIG[tile4.rows]
    db CPU__CPU_NUM_T5_TILECONFIG _AND 0xFF             ; TILECONFIG[tile5.rows]
    db CPU__CPU_NUM_T6_TILECONFIG _AND 0xFF             ; TILECONFIG[tile6.rows]
    db CPU__CPU_NUM_T7_TILECONFIG _AND 0xFF             ; TILECONFIG[tile7.rows]
    db CPU__CPU_NUM_T8_TILECONFIG _AND 0xFF             ; TILECONFIG[tile8.rows]
    db CPU__CPU_NUM_T9_TILECONFIG _AND 0xFF             ; TILECONFIG[tile9.rows]
    db CPU__CPU_NUM_T10_TILECONFIG _AND 0xFF            ; TILECONFIG[tile10.rows]
    db CPU__CPU_NUM_T11_TILECONFIG _AND 0xFF            ; TILECONFIG[tile11.rows]
    db CPU__CPU_NUM_T12_TILECONFIG _AND 0xFF            ; TILECONFIG[tile12.rows]
    db CPU__CPU_NUM_T13_TILECONFIG _AND 0xFF            ; TILECONFIG[tile13.rows]
    db CPU__CPU_NUM_T14_TILECONFIG _AND 0xFF            ; TILECONFIG[tile14.rows]
    db CPU__CPU_NUM_T15_TILECONFIG _AND 0xFF            ; TILECONFIG[tile15.rows]

    org XSAVE_XTILEDATA_STATE_OFFSET
    dz CPU__CPU_NUM_T0_15                               ; TMM0
    dz CPU__CPU_NUM_T0_14
    dz CPU__CPU_NUM_T0_13
    dz CPU__CPU_NUM_T0_12
    dz CPU__CPU_NUM_T0_11
    dz CPU__CPU_NUM_T0_10
    dz CPU__CPU_NUM_T0_09
    dz CPU__CPU_NUM_T0_08
    dz CPU__CPU_NUM_T0_07
    dz CPU__CPU_NUM_T0_06
    dz CPU__CPU_NUM_T0_05
    dz CPU__CPU_NUM_T0_04
    dz CPU__CPU_NUM_T0_03
    dz CPU__CPU_NUM_T0_02
    dz CPU__CPU_NUM_T0_02
    dz CPU__CPU_NUM_T0_00
    dz CPU__CPU_NUM_T1_15                               ; TMM1
    dz CPU__CPU_NUM_T1_14
    dz CPU__CPU_NUM_T1_13
    dz CPU__CPU_NUM_T1_12
    dz CPU__CPU_NUM_T1_11
    dz CPU__CPU_NUM_T1_10
    dz CPU__CPU_NUM_T1_09
    dz CPU__CPU_NUM_T1_08
    dz CPU__CPU_NUM_T1_07
    dz CPU__CPU_NUM_T1_06
    dz CPU__CPU_NUM_T1_05
    dz CPU__CPU_NUM_T1_04
    dz CPU__CPU_NUM_T1_03
    dz CPU__CPU_NUM_T1_02
    dz CPU__CPU_NUM_T1_01
    dz CPU__CPU_NUM_T1_00
    dz CPU__CPU_NUM_T2_15                               ; TMM2
    dz CPU__CPU_NUM_T2_14
    dz CPU__CPU_NUM_T2_13
    dz CPU__CPU_NUM_T2_12
    dz CPU__CPU_NUM_T2_11
    dz CPU__CPU_NUM_T2_10
    dz CPU__CPU_NUM_T2_09
    dz CPU__CPU_NUM_T2_08
    dz CPU__CPU_NUM_T2_07
    dz CPU__CPU_NUM_T2_06
    dz CPU__CPU_NUM_T2_05
    dz CPU__CPU_NUM_T2_04
    dz CPU__CPU_NUM_T2_03
    dz CPU__CPU_NUM_T2_02
    dz CPU__CPU_NUM_T2_01
    dz CPU__CPU_NUM_T2_00
    dz CPU__CPU_NUM_T3_15                               ; TMM3
    dz CPU__CPU_NUM_T3_14
    dz CPU__CPU_NUM_T3_13
    dz CPU__CPU_NUM_T3_12
    dz CPU__CPU_NUM_T3_11
    dz CPU__CPU_NUM_T3_10
    dz CPU__CPU_NUM_T3_09
    dz CPU__CPU_NUM_T3_08
    dz CPU__CPU_NUM_T3_07
    dz CPU__CPU_NUM_T3_06
    dz CPU__CPU_NUM_T3_05
    dz CPU__CPU_NUM_T3_04
    dz CPU__CPU_NUM_T3_03
    dz CPU__CPU_NUM_T3_02
    dz CPU__CPU_NUM_T3_01
    dz CPU__CPU_NUM_T3_00
    dz CPU__CPU_NUM_T4_15                               ; TMM4
    dz CPU__CPU_NUM_T4_14
    dz CPU__CPU_NUM_T4_13
    dz CPU__CPU_NUM_T4_12
    dz CPU__CPU_NUM_T4_11
    dz CPU__CPU_NUM_T4_10
    dz CPU__CPU_NUM_T4_09
    dz CPU__CPU_NUM_T4_08
    dz CPU__CPU_NUM_T4_07
    dz CPU__CPU_NUM_T4_06
    dz CPU__CPU_NUM_T4_05
    dz CPU__CPU_NUM_T4_04
    dz CPU__CPU_NUM_T4_03
    dz CPU__CPU_NUM_T4_02
    dz CPU__CPU_NUM_T4_01
    dz CPU__CPU_NUM_T4_00
    dz CPU__CPU_NUM_T5_15                               ; TMM5
    dz CPU__CPU_NUM_T5_14
    dz CPU__CPU_NUM_T5_13
    dz CPU__CPU_NUM_T5_12
    dz CPU__CPU_NUM_T5_11
    dz CPU__CPU_NUM_T5_10
    dz CPU__CPU_NUM_T5_09
    dz CPU__CPU_NUM_T5_08
    dz CPU__CPU_NUM_T5_07
    dz CPU__CPU_NUM_T5_06
    dz CPU__CPU_NUM_T5_05
    dz CPU__CPU_NUM_T5_04
    dz CPU__CPU_NUM_T5_03
    dz CPU__CPU_NUM_T5_02
    dz CPU__CPU_NUM_T5_01
    dz CPU__CPU_NUM_T5_00
    dz CPU__CPU_NUM_T6_15                               ; TMM6
    dz CPU__CPU_NUM_T6_14
    dz CPU__CPU_NUM_T6_13
    dz CPU__CPU_NUM_T6_12
    dz CPU__CPU_NUM_T6_11
    dz CPU__CPU_NUM_T6_10
    dz CPU__CPU_NUM_T6_09
    dz CPU__CPU_NUM_T6_08
    dz CPU__CPU_NUM_T6_07
    dz CPU__CPU_NUM_T6_06
    dz CPU__CPU_NUM_T6_05
    dz CPU__CPU_NUM_T6_04
    dz CPU__CPU_NUM_T6_03
    dz CPU__CPU_NUM_T6_02
    dz CPU__CPU_NUM_T6_01
    dz CPU__CPU_NUM_T6_00
    dz CPU__CPU_NUM_T7_15                               ; TMM7
    dz CPU__CPU_NUM_T7_14
    dz CPU__CPU_NUM_T7_13
    dz CPU__CPU_NUM_T7_12
    dz CPU__CPU_NUM_T7_11
    dz CPU__CPU_NUM_T7_10
    dz CPU__CPU_NUM_T7_09
    dz CPU__CPU_NUM_T7_08
    dz CPU__CPU_NUM_T7_07
    dz CPU__CPU_NUM_T7_06
    dz CPU__CPU_NUM_T7_05
    dz CPU__CPU_NUM_T7_04
    dz CPU__CPU_NUM_T7_03
    dz CPU__CPU_NUM_T7_02
    dz CPU__CPU_NUM_T7_01
    dz CPU__CPU_NUM_T7_00

    org XSAVE_XTILEDATA2_STATE_OFFSET

    dz CPU__CPU_NUM_T8_15                               ; TMM8
    dz CPU__CPU_NUM_T8_14
    dz CPU__CPU_NUM_T8_13
    dz CPU__CPU_NUM_T8_12
    dz CPU__CPU_NUM_T8_11
    dz CPU__CPU_NUM_T8_10
    dz CPU__CPU_NUM_T8_09
    dz CPU__CPU_NUM_T8_08
    dz CPU__CPU_NUM_T8_07
    dz CPU__CPU_NUM_T8_06
    dz CPU__CPU_NUM_T8_05
    dz CPU__CPU_NUM_T8_04
    dz CPU__CPU_NUM_T8_03
    dz CPU__CPU_NUM_T8_02
    dz CPU__CPU_NUM_T8_01
    dz CPU__CPU_NUM_T8_00
    dz CPU__CPU_NUM_T9_15                               ; TMM9
    dz CPU__CPU_NUM_T9_14
    dz CPU__CPU_NUM_T9_13
    dz CPU__CPU_NUM_T9_12
    dz CPU__CPU_NUM_T9_11
    dz CPU__CPU_NUM_T9_10
    dz CPU__CPU_NUM_T9_09
    dz CPU__CPU_NUM_T9_08
    dz CPU__CPU_NUM_T9_07
    dz CPU__CPU_NUM_T9_06
    dz CPU__CPU_NUM_T9_05
    dz CPU__CPU_NUM_T9_04
    dz CPU__CPU_NUM_T9_03
    dz CPU__CPU_NUM_T9_02
    dz CPU__CPU_NUM_T9_01
    dz CPU__CPU_NUM_T9_00
    dz CPU__CPU_NUM_T10_15                               ; TMM10
    dz CPU__CPU_NUM_T10_14
    dz CPU__CPU_NUM_T10_13
    dz CPU__CPU_NUM_T10_12
    dz CPU__CPU_NUM_T10_11
    dz CPU__CPU_NUM_T10_10
    dz CPU__CPU_NUM_T10_09
    dz CPU__CPU_NUM_T10_08
    dz CPU__CPU_NUM_T10_07
    dz CPU__CPU_NUM_T10_06
    dz CPU__CPU_NUM_T10_05
    dz CPU__CPU_NUM_T10_04
    dz CPU__CPU_NUM_T10_03
    dz CPU__CPU_NUM_T10_02
    dz CPU__CPU_NUM_T10_01
    dz CPU__CPU_NUM_T10_00
    dz CPU__CPU_NUM_T11_15                               ; TMM11
    dz CPU__CPU_NUM_T11_14
    dz CPU__CPU_NUM_T11_13
    dz CPU__CPU_NUM_T11_12
    dz CPU__CPU_NUM_T11_11
    dz CPU__CPU_NUM_T11_10
    dz CPU__CPU_NUM_T11_09
    dz CPU__CPU_NUM_T11_08
    dz CPU__CPU_NUM_T11_07
    dz CPU__CPU_NUM_T11_06
    dz CPU__CPU_NUM_T11_05
    dz CPU__CPU_NUM_T11_04
    dz CPU__CPU_NUM_T11_03
    dz CPU__CPU_NUM_T11_02
    dz CPU__CPU_NUM_T11_01
    dz CPU__CPU_NUM_T11_00
    dz CPU__CPU_NUM_T12_15                               ; TMM12
    dz CPU__CPU_NUM_T12_14
    dz CPU__CPU_NUM_T12_13
    dz CPU__CPU_NUM_T12_12
    dz CPU__CPU_NUM_T12_11
    dz CPU__CPU_NUM_T12_10
    dz CPU__CPU_NUM_T12_09
    dz CPU__CPU_NUM_T12_08
    dz CPU__CPU_NUM_T12_07
    dz CPU__CPU_NUM_T12_06
    dz CPU__CPU_NUM_T12_05
    dz CPU__CPU_NUM_T12_04
    dz CPU__CPU_NUM_T12_03
    dz CPU__CPU_NUM_T12_02
    dz CPU__CPU_NUM_T12_01
    dz CPU__CPU_NUM_T12_00
    dz CPU__CPU_NUM_T13_15                               ; TMM13
    dz CPU__CPU_NUM_T13_14
    dz CPU__CPU_NUM_T13_13
    dz CPU__CPU_NUM_T13_12
    dz CPU__CPU_NUM_T13_11
    dz CPU__CPU_NUM_T13_10
    dz CPU__CPU_NUM_T13_09
    dz CPU__CPU_NUM_T13_08
    dz CPU__CPU_NUM_T13_07
    dz CPU__CPU_NUM_T13_06
    dz CPU__CPU_NUM_T13_05
    dz CPU__CPU_NUM_T13_04
    dz CPU__CPU_NUM_T13_03
    dz CPU__CPU_NUM_T13_02
    dz CPU__CPU_NUM_T13_01
    dz CPU__CPU_NUM_T13_00
    dz CPU__CPU_NUM_T14_15                               ; TMM14
    dz CPU__CPU_NUM_T14_14
    dz CPU__CPU_NUM_T14_13
    dz CPU__CPU_NUM_T14_12
    dz CPU__CPU_NUM_T14_11
    dz CPU__CPU_NUM_T14_10
    dz CPU__CPU_NUM_T14_09
    dz CPU__CPU_NUM_T14_08
    dz CPU__CPU_NUM_T14_07
    dz CPU__CPU_NUM_T14_06
    dz CPU__CPU_NUM_T14_05
    dz CPU__CPU_NUM_T14_04
    dz CPU__CPU_NUM_T14_03
    dz CPU__CPU_NUM_T14_02
    dz CPU__CPU_NUM_T14_01
    dz CPU__CPU_NUM_T14_00
    dz CPU__CPU_NUM_T15_15                               ; TMM15
    dz CPU__CPU_NUM_T15_14
    dz CPU__CPU_NUM_T15_13
    dz CPU__CPU_NUM_T15_12
    dz CPU__CPU_NUM_T15_11
    dz CPU__CPU_NUM_T15_10
    dz CPU__CPU_NUM_T15_09
    dz CPU__CPU_NUM_T15_08
    dz CPU__CPU_NUM_T15_07
    dz CPU__CPU_NUM_T15_06
    dz CPU__CPU_NUM_T15_05
    dz CPU__CPU_NUM_T15_04
    dz CPU__CPU_NUM_T15_03
    dz CPU__CPU_NUM_T15_02
    dz CPU__CPU_NUM_T15_01
    dz CPU__CPU_NUM_T15_00
