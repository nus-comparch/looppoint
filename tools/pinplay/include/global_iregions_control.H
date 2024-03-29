/*BEGIN_LEGAL 
Intel Open Source License 

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
#ifndef GLOBAL_IREGIONS_CONTROL_H
#define GLOBAL_IREGIONS_CONTROL_H

/*! @defgroup CONTROLLER_GLOBAL_IREGIONS
  @ingroup CONTROLLER
   Controller for "regions" that are specified using instruction counts.
   Use -regions:in regions.csv

   regions.csv files will be an alternative to PinPoints files.
   The main goal is to separate warm-up specification from region description. 
   Another major goal is the simplicity of implementation. 

   Regions are specified using a text file with the records of the form:
   comment,thread-id,region-id,simulation-region-start-icount,
   simulation-region-end-icount,region-weight

   [ fields after the first six are ignored, so are lines beginning with '#' ]

   Knobs:
   ------
    -regions:in foo.csv : input file
    -regions:warmup N : use N instructions for warmup
    -regions:prolog N : use N instructions for prolog 
    -regions:epilog N : use N instructions for epilog 
    -regions:verbose : for getting informed about regions/events 
    -regions:overlap-ok : allow overlap among multiple regions.
    -regions:out : Output file for regions skipped due to overlap 
        (if overlap is not ok)
        The idea is to feed this file with "-regions:in" to the next 
        invocation of the tool to process skipped regions.
        * If this knob is specified but no regions are skipped, the output
          file will be empty.

    Region working with the controller:
    -----------------
          1. IREGION class reads region data from file.
          2. Region events are sorted according to icount and type.
          3. Each region event is translated into controller event string like: start:icount:100:tid0
          4. The events will be triggered by the controller ICOUNT alarms mechanism.
          5. The controller will notify IREGION class of the events.
          6. Modify driver not to allow IREGION events and controller events.

    Region processing:
    -----------------
    * The overall regions picture looks as follows:
        WARMUP--PROLOG--(SIM)REGION--EPILOG

        each sub-region has a start and end event. So there are eight 
        events possible (some coinciding e.g. warmup-end and prolog-start)
            EVENT_WARMUP_START  : Beginning of warmup region
            EVENT_WARMUP_STOP  : End of warmup region
            EVENT_PROLOG_START : Beginning of prolog  region
            EVENT_PROLOG_STOP  : End of prolog region
            EVENT_START        : Beginning of interval
            EVENT_STOP         : End of interval
            EVENT_EPILOG_START : Beginning of epilog region
            EVENT_EPILOG_STOP  : End of epilog region

    * Using the warmup/prolog/epilog knobs provided to the controller,
       the region boundaries for the four sub-regions above are computed for
       each record in the regions.csv file.

     * If overlap is not allowed (-regions:overlap-ok is zero), any record 
       that has any of its 4 sub-regions overapping with any sub-region of 
       previously processed records will be ignored. If -regions:out knob 
       is specified, the skipped records will be output to a file. The
       idea is to feed the skipped region records to another invocation of the
       tool involved iteratively till all the records are processed.
    
    * As regions are processed, an event list containing  tuples of the form
     (icount, event-type, region-pointer) is created per thread. There is
      one tuple for each of the possible 8 events for four sub-regions.
*/

#include <algorithm>
#include <sstream> 
#include <string.h>
#include <cctype>
#include "region_utils.H"

using namespace std;
namespace CONTROLLER{
class GLOBALIREGION
{
    private:   
        friend class CONTROL_GLOBALIREGIONS; // allow it to set private fields
        UINT64 _icountStart; // read in
        UINT64 _icountEnd; // read in
        double _weight; // read in
        string _comment; // read in
        UINT32 _rid; // read in
        UINT32 _tid; // read in
        size_t _rno;  // assigned
        UINT64 _warmup_length; // computed + assigned
        UINT64 _prolog_length; // computed + assigned
        UINT64 _epilog_length; // computed + assigned
        UINT32 _weightTimesHundredThousand; // computed + assigned
         // Convert input weight ('double' 0--1)  to  UINT32 to avoid
         // floating point code in the pintools.
        BOOL _isGlobal;
    public:
        GLOBALIREGION()
        {
            _icountStart = 0; 
            _icountEnd = 0; 
            _weight = 0; 
            _rid = 0; 
            _tid = 0 ; 
            _rno = 0; 
            _warmup_length = 0;
            _prolog_length = 0;
            _epilog_length = 0;
            _weightTimesHundredThousand = 0;
            _isGlobal = FALSE;
        }
        string GetComment() const { return _comment;}
        UINT32 GetRegionId() const { return _rid;}
        UINT64 GetRegionStartICount() const { return _icountStart; }
        BOOL IsGlobalRegion() const { return _isGlobal; }
        UINT64 GetRegionEndICount() const { return _icountEnd; }
        UINT64 GetWarmupLength() const { return _warmup_length; }
        UINT64 GetPrologLength() const { return _prolog_length; }
        UINT64 GetRegionLength() const { return _icountEnd - _icountStart; }
        UINT64 GetEpilogLength() const { return _epilog_length;}
        UINT32 GetWeightTimesHundredThousand() const {
            return _weightTimesHundredThousand;}
        VOID SetICountEnd(UINT64 icountEnd) {_icountEnd = icountEnd;}
        VOID SetEpilogLength(UINT64 epilog_length) {_epilog_length = epilog_length;}
};

class GIEVENT
{
    public:
        GIEVENT()
        {
            icount = 0;
            type = EVENT_INVALID;
            iregion = (class GLOBALIREGION *) NULL;
        }
        static BOOL EventLessThan (const GIEVENT & a, const GIEVENT & b)
        {
            BOOL retval = false;
            if(a.icount == b.icount)
            {
                if (b.type == EVENT_WARMUP_START)
                {
                    if ((a.type == EVENT_WARMUP_START))
                    {
                        retval =  true;
                    }    
                }
                else if (b.type == EVENT_WARMUP_STOP)
                {
                    if ((a.type == EVENT_WARMUP_START) || 
                        (a.type == EVENT_WARMUP_STOP))
                    {
                        retval =  true;
                    }    
                }
                else if (b.type == EVENT_PROLOG_START)
                {
                    if ((a.type == EVENT_WARMUP_START) || 
                        (a.type == EVENT_WARMUP_STOP) || 
                        (a.type == EVENT_PROLOG_START))
                    {
                        retval =  true;
                    }    
                }
                else if (b.type == EVENT_PROLOG_STOP)
                {
                    if ((a.type == EVENT_WARMUP_START) || 
                        (a.type == EVENT_WARMUP_STOP) || 
                        (a.type == EVENT_PROLOG_START) || 
                        (a.type == EVENT_PROLOG_STOP))
                    {
                        retval =  true;
                    }    
                }
                else if (b.type == EVENT_START)
                {
                    retval = true;
                    if ((a.type == EVENT_STOP) || 
                        (a.type == EVENT_EPILOG_START) || 
                        (a.type == EVENT_EPILOG_STOP))
                    {
                        retval =  false;
                    }    
                }
                else if (b.type == EVENT_STOP)
                {
                    retval = true;
                    if ((a.type == EVENT_EPILOG_START) || 
                        (a.type == EVENT_EPILOG_STOP))
                    {
                        retval =  false;
                    }    
                }
                else if (b.type == EVENT_EPILOG_START)
                {
                    retval = true;
                    if ((a.type == EVENT_EPILOG_STOP))
                    {
                        retval =  false;
                    }    
                }
                else if (b.type == EVENT_EPILOG_STOP)
                {
                    retval =  true;
                }
                else{
                    retval =  true;
                }
                return retval;
            }
            return a.icount < b.icount;
        }

        static const CHAR * EventToString(EVENT_TYPE type)
        {
            switch(type)
            {
                case EVENT_THREADID : return "control-threadid";
                case EVENT_START : return "region-start";
                case EVENT_STOP : return "region-end";
                case EVENT_WARMUP_START : return "warmup-start";
                case EVENT_WARMUP_STOP : return "warmup-end";
                case EVENT_PROLOG_START : return "prolog-start";
                case EVENT_PROLOG_STOP : return "prolog-end";
                case EVENT_EPILOG_START : return "epilog-start";
                case EVENT_EPILOG_STOP : return "epilog-end";
                default: return "invalid";
            }
        }

    private:
        friend class CONTROL_GLOBALIREGIONS; // allow it to set private fields
        UINT64 icount;
        EVENT_TYPE type;
        class GLOBALIREGION * iregion;
};

typedef vector<GLOBALIREGION> GLOBALIREGION_VECTOR;
typedef vector<GIEVENT> GIEVENT_VECTOR;

/*! @ingroup CONTROLLER_GLOBALIREGIONS
*/

class CONTROL_GLOBALIREGIONS
{
    private:
    static const UINT32 BUFSIZE=2000;  

    public:
    CONTROL_GLOBALIREGIONS(CONTROL_ARGS & control_args)
        : _control_args(control_args),
          _giFileKnob(KNOB_MODE_WRITEONCE,
                     control_args.get_knob_family(),
                     "iregions:in",
                     "",
                     "Regions file",
                     control_args.get_prefix()),
         _giWarmupKnob(KNOB_MODE_WRITEONCE,
                      control_args.get_knob_family(),
                      "iregions:warmup",
                      "0",
                      "# of instructions in the warm-up region",
                      control_args.get_prefix()),
          _giPrologKnob(KNOB_MODE_WRITEONCE,
                       control_args.get_knob_family(),
                       "iregions:prolog",
                       "0",
                       "# of instructions in the prolog region",
                       control_args.get_prefix()),
          _giEpilogKnob(KNOB_MODE_WRITEONCE,
                       control_args.get_knob_family(),
                       "iregions:epilog",
                       "0",
                       "# of instructions in the epilog region",
                       control_args.get_prefix()),
          _giVerboseKnob(KNOB_MODE_WRITEONCE,
                        control_args.get_knob_family(),
                        "iregions:verbose",
                        "0",
                        "Print information about regions/events ",
                        control_args.get_prefix()),
          _giOverlapOkKnob(KNOB_MODE_WRITEONCE,
                          control_args.get_knob_family(),
                          "iregions:overlap-ok",
                          "0",
                          "Allow overlap in regions.",
                          control_args.get_prefix()),
          _giOutFileKnob(KNOB_MODE_WRITEONCE,
                        control_args.get_knob_family(),
                        "iregions:out",
                        "",
                        "Output file containing regions skipped due to overlap",
                        control_args.get_prefix())
    {
        _valid = true;
        _isGlobal = false;
        _maxThreads = PIN_MAX_THREADS;
        _xcount = 0;
        _last_triggered_iregionGlobal = NULL;
        _passContext = FALSE;
        _active = false;
    }

    /*! @ingroup CONTROLLER_GLOBALIREGIONS
      Activate the controller if the -regions knob is provided
      @return 1 if controller can start an interval, otherwise 0
    */
    INT32 Activate(CONTROL_MANAGER* cm )
    {
        _cm = cm;
        if (strcmp(_giFileKnob.Value().c_str(),"") == 0)
        {
            return 0;
        }
        _passContext = TRUE;
        _active = true;

        if (strcmp(_giOutFileKnob.Value().c_str(),"") != 0)
        {
            xfile.open(_giOutFileKnob.Value().c_str());
            if (!xfile.is_open())
            {
                cerr << "Could not open output  file " << 
                    _giOutFileKnob.Value().c_str() << endl;
                PIN_ExitApplication(-1);
            }
        }

        Allocate();

        ReadRegionsFile();

        ProcessRegions();

        if(_giVerboseKnob) PrintRegions();

        ProcessEvents();

        if(_giVerboseKnob) PrintEvents();

        // Set Region name callback
        _cm->SetRegionInfoCallback(CONTROL_GLOBALIREGIONS::RegionInfoCallback, this);
                // Set external regions
        _cm->AddExternalRegionChains(&_regionControlChains,CONTROL_GLOBALIREGIONS::SetTriggeredRegion,this);


        return TRUE;
    }
    bool IsActive() const { return _active; };
    GLOBALIREGION * LastTriggeredRegion(THREADID tid) const { 
        if(_isGlobal) return _last_triggered_iregionGlobal;
        return _last_triggered_iregion[tid];}

    // Region name callback
    static CONTROL_REGION_INFO RegionInfoCallback(THREADID tid, VOID * region_info_param)  {
        CONTROL_REGION_INFO region_info;
        CONTROL_GLOBALIREGIONS * ci = (CONTROL_GLOBALIREGIONS *)region_info_param;
        GLOBALIREGION * curr_iregion = ci->LastTriggeredRegion(tid);

        // Build the region name
        string weight_string = REGION_UTILS::WeightToString(curr_iregion->GetWeightTimesHundredThousand());
        string tidspec = (curr_iregion->IsGlobalRegion())?"_global":"_t" 
                 + decstr(tid);
        region_info.regionName = tidspec +
            "r" + decstr(curr_iregion->GetRegionId()) +
            "_warmup" + decstr(curr_iregion->GetWarmupLength()) +
            "_prolog" + decstr(curr_iregion->GetPrologLength()) +
            "_region" + decstr(curr_iregion->GetRegionLength()) +
            "_epilog" + decstr(curr_iregion->GetEpilogLength()) +
            "_" + StringDecSigned(curr_iregion->GetRegionId(), 3, '0') +
            "_" + weight_string;
        region_info.regionId = curr_iregion->GetRegionId();

        return region_info;
    }

    // Get the next region event
    static BOOL SetTriggeredRegion(THREADID tid, EVENT_TYPE event_type, VOID* event_handler, VOID* param)  {
    //VOID SetTriggeredRegion(THREADID tid, VOID* event_handler)  { 

        ASSERT(param, "PARAM is NULL.");
        ASSERT(event_handler, "GLOBALIREGION is NULL.");

        CONTROL_GLOBALIREGIONS * control_iregions = (CONTROL_GLOBALIREGIONS *)param;
        GLOBALIREGION * iregion = (GLOBALIREGION *)event_handler;

        if(control_iregions->_isGlobal)
        {
          control_iregions->_last_triggered_iregionGlobal = iregion;
        }
        else
        {
          control_iregions->_last_triggered_iregion[tid] = iregion;
        }
        return TRUE;
    }

    private:
    CONTROL_ARGS _control_args;
    bool _valid;
    CONTROLLER::CONTROL_MANAGER* _cm;

    // Allocate control regions data structures
    VOID Allocate()
    {
        _iregions = new GLOBALIREGION_VECTOR[_maxThreads];
        _events = new GIEVENT_VECTOR[_maxThreads];
        _last_triggered_iregion = new GLOBALIREGION * [_maxThreads];
        memset(_last_triggered_iregion , 0, 
            sizeof(_last_triggered_iregion[0]) * _maxThreads);
    }

    VOID ReadRegionsFile()
    {
        string filename = _giFileKnob.Value().c_str();

        ifstream rfile(filename.c_str());

        if (!rfile.is_open())
        {
            cerr << "Could not open regions file " << 
                _giFileKnob.Value().c_str() << endl;
            PIN_ExitApplication(-1);
        }

        UINT32 lineNum = 0;
        UINT32 recordNum = 0;
        GLOBALIREGION * region = 0;
        while(true)
        {
            if( rfile.eof() )
            {
                break;
            }

            UINT32 recordLen = 0;
            CHAR record[BUFSIZE+1];
            CHAR urecord[BUFSIZE+1];
            string field;

            double t_weight;
            string t_comment;
            INT32 t_rid;
            INT32 t_tid = 0;
            UINT64 t_icountStart;
            UINT64 t_icountEnd;

            rfile.getline(record, BUFSIZE);
            lineNum++;

            recordLen = strnlen_s(record, BUFSIZE+1);
            if (recordLen == 0) continue;

            // Create a temporary record with lower case letters
            for (UINT32 i = 0; i <= recordLen; i++) 
                urecord[i] = tolower(record[i]);

            // first word "comment" : this is the header
            if(strncmp(urecord,"comment",7)==0) continue;

            // first letter '#' : this is a comment 
            if(urecord[0]=='#') continue;

            istringstream s(record);
            recordNum++;


            // cerr << "Record # " << recordNum << endl;
            field.clear();
            getline(s, field, ',');
            ASSERT(!field.empty(), "Empty comment field.");
            t_comment = field;
            // cerr << "Comment " << t_comment << endl;

            field.clear();
            getline(s, field, ',');
            ASSERT(!field.empty(), "Empty thread-id field.");
            if(!_isGlobal && strncmp(field.c_str(),"global",6)==0)
            {
                  _isGlobal = true;
            }
            if (! _isGlobal )
            {
                  t_tid = REGION_UTILS::StringToUINT32(field, "thread-id");
            }
            // cerr << "thread-id " << t_tid << endl;

            field.clear();
            getline(s, field, ',');
            ASSERT(!field.empty(), "Empty region-id field.");
            t_rid = REGION_UTILS::StringToUINT32(field, "region-id");
            //cerr << "region-id " << t_rid << endl;

            field.clear();
            getline(s, field, ',');
            ASSERT(!field.empty(), "Empty start-icount field.");
            istringstream sistart(field);
            t_icountStart  = REGION_UTILS::StringToUINT64(field, 
                                            "simulation-region-start-icount");
            //cerr << "start-icount " << t_icountStart << endl;

            field.clear();
            getline(s, field, ',');
            ASSERT(!field.empty(), "Empty end-icount field.");
            t_icountEnd  = REGION_UTILS::StringToUINT64(field, 
                                          "simulation-region-end-icount");
            //cerr << "end-icount " << siend << endl;

            ASSERT(t_icountEnd > t_icountStart , 
                   "simulation-region-start-icount:"  + 
                   decstr(t_icountStart)  + 
                   " is not smaller than simulation-region-end-icount:" 
                   + decstr(t_icountEnd) );

            field.clear();
            getline(s, field, ',');
            ASSERT(!field.empty(), "Empty region-weight field.");
            t_weight  = REGION_UTILS::StringToDouble(field, "region-weight");
            ASSERT((t_weight >= 0), 
                    "region-weight (" + field + ") must be positive" );
            ASSERT((t_weight <= 1), 
                    "region-weight (" + field + ") must be between 0 and 1" );
            //cerr << "region-weight" << t_weight << endl;

            string tail;

            s >> tail;

            if(!tail.empty())
                cerr << "WARNING: regions:in file '" << filename << 
                    "' line number " << dec << lineNum << 
                    ": ignoring fields : " << tail  << endl;


            if(_isGlobal)
            {
                  _iregionsGlobal.push_back(GLOBALIREGION());
                  region = & _iregionsGlobal.back();
                  region->_isGlobal = true;
                  region->_tid = -1;
            }
            else
            {
                ASSERTX(t_tid>=0 && (UINT32)t_tid<_maxThreads);
                _iregions[t_tid].push_back(GLOBALIREGION());
                region = & _iregions[t_tid].back();
                region->_tid = t_tid;
            }

            region->_comment = t_comment;
            region->_rno = _iregions[t_tid].size();
            region->_rid = t_rid;
            region->_weight = t_weight;
            region->_weightTimesHundredThousand = (UINT32)(t_weight*100000);
            region->_icountStart = t_icountStart;
            region->_icountEnd = t_icountEnd;
        }
        rfile.close();
    }

    VOID PrintRegions()
    {
        for(UINT32 tid=0; tid < _maxThreads; tid++)
        {
            for ( UINT32 i = 0; i < _iregions[tid].size(); i++ )
            {
                GLOBALIREGION * region = & _iregions[tid][i];
                cerr << "region pointer: " << region
                << " rno: " << region->_rno
                << " comment " << region->_comment
                << " rid " << region->_rid
                << " tid " << region->_tid
                << " weight " << region->_weight
                << " weightTimesHundredThousand " 
                << region->_weightTimesHundredThousand
                << " icountStart " << region->_icountStart
                << " icountEnd " << region->_icountEnd
                << " warmup_length " << region->_warmup_length
                << " prolog_length " << region->_prolog_length
                << " region_length " << region->GetRegionLength()
                << " epilog_length " << region->_epilog_length
                << endl;
            }
        }

    }

    BOOL RegionHasOverlap(GIEVENT_VECTOR iev, UINT64 span_begin, UINT64 span_end)
    {
        if(_giOverlapOkKnob) return false;
        for ( UINT32 i = 0; i < iev.size(); i++ )
        {
                GIEVENT * event = & iev[i];
                if((span_begin <= event->icount) && (span_end >= event->icount))
                {
                    if (xfile.is_open())
                    {
                        if(_xcount==0) 
                            xfile << "comment,thread-id,region-id,"
                            << "simulation-region-start-icount,"
                            << "simulation-region-end-icount,region-weight" 
                            << endl;
                        xfile << "#expanded region " << dec << span_begin 
                            << ":" << dec << span_end 
                            << " overlapped with event " 
                            << GIEVENT::EventToString(event->type) << " at " 
                            << dec << event->icount << endl; 
                        _xcount++;
                    }
                    return true;
                }
        }
        return false;
    }

    VOID PrintEventVector(GIEVENT_VECTOR iv, INT32 tid=-1)
    {
      for ( UINT32 i = 0; i < iv.size(); i++ )
      {
        GIEVENT * event = & iv[i];
        string tidstr = _isGlobal ? "global": ("tid"+decstr(tid));
        cerr << tidstr << " event " 
          << GIEVENT::EventToString(event->type) << " at " 
          << dec << event->icount << endl; 
      }
    }

    VOID PrintEvents()
    {
        cerr << "Events:" << endl;
     
        if(_isGlobal)
        {
          PrintEventVector(_eventsGlobal);
        }
        else
        {
          for(UINT32 tid=0; tid < _maxThreads; tid++)
          {
            PrintEventVector(_events[tid]);
          }
        }
    }

    VOID ProcessEventsVector(GIEVENT_VECTOR *irv, INT32 tid=-1)
    {
      sort(irv->begin(), irv->end(), GIEVENT::EventLessThan);

      // Add to controller strings
      for ( UINT32 i = 0; i < irv->size(); i++ )
      {
        GIEVENT * event = & (*irv)[i];
        CHAIN_EVENT chain_event;
        chain_event.event_handler = event->iregion;
        if(_isGlobal)
        {
          chain_event.chain_str = _cm->EventToString(event->type)+
                    ":icount:"+decstr(event->icount)+":global";
        }
        else
        {
          chain_event.chain_str = _cm->EventToString(event->type)+
                    ":icount:"+decstr(event->icount)+":tid"+decstr(tid);
        }
        // Added for fixing JIRA SDE-2585 
        chain_event.tid = tid;
        _regionControlChains.push_back(chain_event);
      }
    }

    // Sort the events according to their type and icount
    // Prepare controller events strings
    VOID ProcessEvents()
    {
        if(_isGlobal)
        {
          ProcessEventsVector(&_eventsGlobal);
        }
        else
        {
          for(UINT32 tid=0; tid < _maxThreads; tid++)
          {
            ProcessEventsVector(&_events[tid], tid);
          }
        }
    }

    // Add an event to the events vector
    VOID InsertOneEvent(UINT32 tid, UINT64 icount, 
                        EVENT_TYPE type, GLOBALIREGION * region)
    {
        GIEVENT * event = 0;
        if(_isGlobal)
        {
          _eventsGlobal.push_back(GIEVENT());
          event = & _eventsGlobal.back();
        }
        else
        {
          _events[tid].push_back(GIEVENT());
          event = & _events[tid].back();
        }

        event->icount = icount;
        event->type = type;
        event->iregion = region;
    }

    VOID ProcessRegionsVector(GLOBALIREGION_VECTOR *irv, INT32 tid = -1)
    {
      for ( UINT32 i = 0; i < irv->size(); i++ )
      {
        GLOBALIREGION * region = & (*irv)[i];
        UINT64 span_begin = 0;
        UINT64 span_end = 0;

        // cerr << "rno: " << region->_rno
        // << " comment " << region->_comment
        // << " icountStart " << region->_icountStart
        // << " icountEnd " << region->_icountEnd
        // << endl;

        INT64 wstart = region->_icountStart-_giPrologKnob-_giWarmupKnob;
        INT64 wend = region->_icountStart - _giPrologKnob;
        INT64 pstart = wend;
        INT64 pend = region->_icountStart;
        INT64 rstart = pend;
        INT64 estart = region->_icountEnd;
        INT64 rend = estart;
        INT64 eend = region->_icountEnd + _giEpilogKnob;

        if(_giWarmupKnob && (wstart > 0))
        {
          // cerr << "WarmupStart " << dec << wstart << endl;
          // cerr << "WarmupEnd " << dec << wend << endl;
          span_begin = wstart;
        }

        if(_giPrologKnob && (pstart > 0))
        {
          // cerr << "PrologStart " << dec << pstart << endl;
          // cerr << "PrologEnd " << dec << pend << endl;
          if(!span_begin) span_begin = pstart;
        }

        if(!span_begin) span_begin = rstart;
        // cerr << "RegionStart " << dec << rstart << endl;
        // cerr << "RegionEnd " << dec << rend << endl;
        span_end = rend;

        if(_giEpilogKnob && (eend > estart))
        {
          // cerr << "EpilogStart " << dec << estart << endl;
          // cerr << "EpilogEnd " << dec << eend << endl;
          span_end = eend;
        }

        // cerr << "span_begin " << dec << span_begin << endl;
        // cerr << "span_end " << dec << span_end << endl;

        GIEVENT_VECTOR iev;
        if(_isGlobal)
            iev = _eventsGlobal;
        else
            iev = _events[tid];;
        if(RegionHasOverlap(iev, span_begin, span_end))
        {
          // cerr << "Region has overlap" << endl;
          if (xfile.is_open())
          {
            xfile << region->_comment
              << "," << (_isGlobal?"global":decstr(region->_tid))
              << "," << region->_rid
              << "," << region->_icountStart
              << "," << region->_icountEnd
              << "," << region->_weight
              << endl;
          }
        }
        else
        {
          if(_giWarmupKnob && (wstart > 0))
          {
            InsertOneEvent(tid, wstart, EVENT_WARMUP_START, region);
            InsertOneEvent(tid, wend, EVENT_WARMUP_STOP, region);
            region->_warmup_length = wend - wstart;
          }
        if(_giPrologKnob && (pstart > 0))
        {
          InsertOneEvent(tid, pstart, EVENT_PROLOG_START, region);
          InsertOneEvent(tid, pend, EVENT_PROLOG_STOP, region);
          region->_prolog_length = pend - pstart;
        }
        InsertOneEvent(tid, rstart, EVENT_START, region);
        InsertOneEvent(tid, rend, EVENT_STOP, region);
        if(_giEpilogKnob && (eend > estart))
        {
          InsertOneEvent(tid, estart, EVENT_EPILOG_START, region);
          InsertOneEvent(tid, eend, EVENT_EPILOG_STOP, region);
          region->_epilog_length = eend - estart;
        }
      }
    }
   }

    VOID ProcessRegions()
    {
        if(_isGlobal)
        {
            ProcessRegionsVector(&_iregionsGlobal);
        }
        else
        {
          for(UINT32 tid=0; tid < _maxThreads; tid++)
          {
            ProcessRegionsVector(&_iregions[tid], tid);
          }
        }

        if (xfile.is_open())
        {
            if(_xcount) xfile << "#eof" << endl;
            xfile.close();
        }
    }

    KNOB<string> _giFileKnob;
    KNOB<UINT64> _giWarmupKnob;
    KNOB<UINT64> _giPrologKnob;
    KNOB<UINT64> _giEpilogKnob;
    KNOB<BOOL> _giVerboseKnob;
    KNOB<BOOL> _giOverlapOkKnob;
    KNOB<string> _giOutFileKnob;
    GLOBALIREGION_VECTOR *_iregions; // per thread vector containing region info
    GIEVENT_VECTOR *_events;  // per thread list (sorted by icount) of events
    GLOBALIREGION_VECTOR _iregionsGlobal; // global region info
    GIEVENT_VECTOR _eventsGlobal;  // list (sorted by icount) of global events
    bool _active;
    THREADID _maxThreads;
    ofstream xfile;  // for writing out regions excluded due to overlap
    UINT32 _xcount; // number of regions excluded
    GLOBALIREGION ** _last_triggered_iregion;
    GLOBALIREGION * _last_triggered_iregionGlobal;
    BOOL _passContext;
    BOOL _isGlobal;
    CHAIN_EVENT_VECTOR _regionControlChains;
};
}
#endif
