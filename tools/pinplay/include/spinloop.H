/*BEGIN_LEGAL 
BSD License 

Copyright (c) 2020 Intel Corporation. All rights reserved.
 
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.  Redistributions
in binary form must reproduce the above copyright notice, this list of
conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.  Neither the name of
the Intel Corporation nor the names of its contributors may be used to
endorse or promote products derived from this software without
specific prior written permission.
 
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE INTEL OR
ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
END_LEGAL */

#ifndef SPINLOOP_H
#define SPINLOOP_H

/*
*/

#include <algorithm>
#include <sstream> 
#include <fstream> 
#include <iostream> 
#include <cctype>
#include <string>
#include <list>
#include <sys/syscall.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <libgen.h>
#include <fcntl.h>
#include <dirent.h>
#include "pin.H"
#include "instlib.H"

using namespace std;
namespace SPINLOOP_MON{
class SPINLOOP
{
  public:
    SPINLOOP():_knobSpinStartSSC(KNOB_MODE_WRITEONCE,  
    "pintool",
    "spinloop:start_SSC", "0", "SSC marker (0x...) for the start of spin loop to be skipped "),
     _knobSpinEndSSC(KNOB_MODE_WRITEONCE,  
    "pintool",
    "spinloop:end_SSC", "0", "SSC marker (0x...) for the end of spin loop to be skipped ")
    {
    }

    BOOL InsideSpinLoop(THREADID tid)
    {
      return spinActive[tid];
    }

    BOOL Enabled()
    {
      return _knobSpinStartSSC && _knobSpinEndSSC;
    }

    static VOID EnterSpinLoop(THREADID tid, 
            SPINLOOP *sp)
    {
      sp->spinEntryCount[tid]++;
      sp->spinActive[tid] = TRUE;
    }

    static VOID ExitSpinLoop(THREADID tid, 
            SPINLOOP *sp)
    {
      sp->spinExitCount[tid]++;
      sp->spinActive[tid] = FALSE;
    }

    static VOID  CheckSSC(TRACE trace, UINT32 h, SPINLOOP * sp)
    {
      enum CALL_ORDER global_order = (CALL_ORDER)(CALL_ORDER_DEFAULT + 5);
      const UINT32 pattern_len = 8;
      const unsigned int movebx_size = 5;
      const unsigned int special_nop_size = 3;
      unsigned int ins_size = 0 ,next_ins_size = 0;
      EXCEPTION_INFO excep = EXCEPTION_INFO();
      INS ins,next_ins=INS_Invalid();
      //the template of ssc marker
      unsigned char ssc_marker[] = { 0xbb, 0x00, 0x00, 0x00, 0x00,
                                   0x64, 0x67, 0x90};
      for(int j=0;j<4;j++){
        //fill in the ssc value
        ssc_marker[1+j]= (h>>(j*8))&0xff;
      }

      for (BBL bbl = TRACE_BblHead(trace); BBL_Valid(bbl); bbl = BBL_Next(bbl))
      {
        ins = BBL_InsHead(bbl);
        if (INS_Valid(ins))
        {
            ins_size = INS_Size(ins);
            next_ins = INS_Next(ins);
        }
        while (INS_Valid(next_ins))
        {
            next_ins_size = INS_Size(next_ins);
            if (ins_size + next_ins_size == pattern_len)
            {
                unsigned char* pc;
                pc = reinterpret_cast<unsigned char*>(INS_Address(ins));
                            
                unsigned char dst_buf[pattern_len];
                size_t copy_size = PIN_FetchCode(dst_buf, pc, pattern_len, &excep);
                if (copy_size == pattern_len &&  
                  memcmp(ssc_marker,dst_buf,pattern_len) == 0){
                    IPOINT afterpoint;
                    if( BBL_HasFallThrough(bbl))
                      afterpoint = IPOINT_AFTER;
                    else if(INS_IsValidForIpointTakenBranch(BBL_InsTail(bbl))) 
                      afterpoint = IPOINT_TAKEN_BRANCH;
                    else
                      ASSERT(0, "Unable to decide after BBL instrumentation point");
                     
                   if(h==sp->_knobSpinStartSSC)
                   {
                     BBL_InsertCall(bbl, IPOINT_BEFORE,
                        (AFUNPTR)EnterSpinLoop, 
                        IARG_CALL_ORDER, global_order,
                        IARG_THREAD_ID, IARG_PTR, sp, IARG_END);
                     //cerr << "(inside BBL )Found START SSC marker " << std::hex << h << " in Trace " << std::hex << TRACE_Address(trace) << endl;
                   }
                   if(h==sp->_knobSpinEndSSC)
                   {
                     BBL_InsertCall(bbl, afterpoint,
                        (AFUNPTR)ExitSpinLoop, 
                        IARG_CALL_ORDER, global_order,
                        IARG_THREAD_ID, IARG_PTR, sp, IARG_END);
                     //cerr << "(inside BBL )Found END SSC marker " << std::hex << h << " in Trace " << std::hex << TRACE_Address(trace) << endl;
                   }
                }
            }
            ins = next_ins;
            ins_size = next_ins_size;
            next_ins = INS_Next(next_ins);
        }
        
        //For the last instruction in the BBL, we want to check the next
        //instruction, the head of the next BBL.
        if (ins_size == movebx_size)
        {
            BBL next_bbl = BBL_Next(bbl);
            if (BBL_Valid(next_bbl))
            {
                next_ins = BBL_InsHead(next_bbl);
            }
            //If the head of the next BBL can potentailly be joint with the
            //current ins to an ssc_mark, or if this is the last instruction in
            //the trace.
            if (!INS_Valid(next_ins) || INS_Size(next_ins) == special_nop_size)
            {    
                unsigned char* pc;
                pc = reinterpret_cast<unsigned char*>(INS_Address(ins));
                            
                unsigned char dst_buf[pattern_len];
                size_t copy_size = PIN_FetchCode(dst_buf, pc, pattern_len, &excep);
                if (copy_size == pattern_len &&  
                  memcmp(ssc_marker,dst_buf,pattern_len) == 0){
                    IPOINT afterpoint;
                    if( BBL_HasFallThrough(bbl))
                      afterpoint = IPOINT_AFTER;
                    else if(INS_IsValidForIpointTakenBranch(BBL_InsTail(bbl))) 
                      afterpoint = IPOINT_TAKEN_BRANCH;
                    else
                      ASSERT(0, "Unable to decide after BBL instrumentation point");
                   if(h==sp->_knobSpinStartSSC)
                   {
                     BBL_InsertCall(bbl, IPOINT_BEFORE,
                        (AFUNPTR)EnterSpinLoop, 
                        IARG_CALL_ORDER, global_order,
                        IARG_THREAD_ID, IARG_PTR, sp, IARG_END);
                     //cerr << "(end-of BBL )Found START SSC marker " << std::hex << h << " in Trace " << std::hex << TRACE_Address(trace) << endl;
                   }
                   if(h==sp->_knobSpinEndSSC)
                   {
                     BBL_InsertCall(bbl, afterpoint,
                        (AFUNPTR)ExitSpinLoop, 
                        IARG_CALL_ORDER, global_order,
                        IARG_THREAD_ID, IARG_PTR, sp, IARG_END);
                     //cerr << "(end-of BBL )Found END SSC marker " << std::hex << h << " in Trace " << std::hex << TRACE_Address(trace) << endl;
                   }
                }
            }
         }
       }
    }

    static VOID Trace(TRACE trace, VOID *v)
    {
      SPINLOOP * sp = reinterpret_cast<SPINLOOP *>(v);
        
      sp->CheckSSC(trace, sp->_knobSpinStartSSC, sp);
      sp->CheckSSC(trace, sp->_knobSpinEndSSC, sp);
    }

    static VOID ProcessFini(INT32 code, VOID *v)
    {
      SPINLOOP * sp = reinterpret_cast<SPINLOOP *>(v);
        for (THREADID tnum = 0; tnum < PIN_MAX_THREADS; tnum++)
        {   
          if(sp->spinEntryCount[tnum])
          {
            cerr << "tid " << tnum << " Spin Loop Entry count " << std::dec << 
               sp->spinEntryCount[tnum] << endl;
            cerr << "tid " << tnum << " Spin Loop Exit count " << std::dec <<
               sp->spinExitCount[tnum] << endl;
            cerr << "tid " << tnum << " Spin Active flag " << std::dec <<
               sp->spinActive[tnum] << endl;
          }
        }   
    }

    VOID Activate()
    {
      //Want the flags to be available with the default value of FALSE when activated 
      spinActive = new BOOL [PIN_MAX_THREADS];
      memset(spinActive, 0, PIN_MAX_THREADS * sizeof(spinActive[0]));
      // Allocate counters only if relvant knobs are present
      if ( _knobSpinStartSSC &&
                _knobSpinEndSSC )
      {
        spinEntryCount = new UINT64 [PIN_MAX_THREADS];
        memset(spinEntryCount, 0, PIN_MAX_THREADS * sizeof(spinEntryCount[0]));
        spinExitCount = new UINT64 [PIN_MAX_THREADS];
        memset(spinExitCount, 0, PIN_MAX_THREADS * sizeof(spinExitCount[0]));
        PIN_AddFiniFunction(ProcessFini, this);
        TRACE_AddInstrumentFunction(Trace, this);
      }
    }
  private:
    KNOB<UINT32>  _knobSpinStartSSC;
    KNOB<UINT32>  _knobSpinEndSSC;
    UINT64 * spinEntryCount;
    UINT64 * spinExitCount;
    BOOL * spinActive;
};
}
#endif
