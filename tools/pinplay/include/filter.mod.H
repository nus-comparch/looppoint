/*
 * Copyright 2002-2019 Intel Corporation.
 * 
 * This software is provided to you as Sample Source Code as defined in the accompanying
 * End User License Agreement for the Intel(R) Software Development Products ("Agreement")
 * section 1.L.
 * 
 * This software and the related documents are provided as is, with no express or implied
 * warranties, other than those that are expressly stated in the License.
 */

#ifndef FILTER_MOD_H
#define FILTER_MOD_H

#include "pin.H"
using std::string;
namespace INSTLIB 
{

/*! @defgroup FILTER_MOD

  Filters are used to select static parts of the program to instrument. A
  user may only want to instrument specific routines or may way to ignore
  shared libraries.

  The example below can be foundin InstLibExamples/filter.cpp

  \include filter.cpp
  
*/
  
/*! @defgroup FILTER_MOD_RTN
  @ingroup FILTER_MOD
  Filter for selecting routines by name
  Use -filter_rtn <name> to select a routine. To select multiple routines, use more than one -filter_rtn.
*/


/*! @defgroup FILTER_MOD_RTN
  @ingroup FILTER_MOD
  Filter for selecting routines by name
  Use -filter_rtn <name> to select a routine. To select multiple routines, use more than one -filter_rtn.
*/

/*! @ingroup FILTER_MOD_RTN
*/
class FILTER_MOD_RTN
{
  public:
    FILTER_MOD_RTN(const string& prefix="", const string& knob_family="pintool") : 
        _rtnsKnob(KNOB_MODE_APPEND, knob_family, prefix+"filter_rtn", "", 
                  "Routines to instrument"),
        _rtnExcludeKnob(KNOB_MODE_APPEND, knob_family, prefix+"filter_exclude_rtn", "", 
                  "Routine to NOT instrument") 
    {}
    
    /*! @ingroup FILTER_MOD_RTN
      Activate the filter. Must be done before PIN_StartProgram
    */
    VOID Activate()
    {
        PIN_InitSymbols();
        _activated = true;
    }
    
    /*! @ingroup FILTER_MOD_RTN
      Return true if the filter is not active or the routine that contains this trace is selected
    */
    BOOL SelectTrace(TRACE trace)
    {
        ASSERTX(_activated);
        
        if (!RTN_Valid(TRACE_Rtn(trace)))
        {
            if (_rtnsKnob.NumberOfValues() > 0)
                return false;
            else
                return true;
        }
        
        return SelectRtn(TRACE_Rtn(trace));
    }

    /*! @ingroup FILTER_MOD_RTN
      Return true if the filter is not active or the routine is selected
    */
    BOOL SelectRtn(RTN rtn)
    {
        ASSERTX(RTN_Valid(rtn));
        ASSERTX(_activated);

        UINT32 numRtns = _rtnsKnob.NumberOfValues();
        UINT32 numExcludeRtns = _rtnExcludeKnob.NumberOfValues();
        
         // No explicit inclusion or exclusion list hence all rtns  included
        if ((numRtns == 0) && (numExcludeRtns == 0))
            return true;

        if (numExcludeRtns)
        {
          // Some routines are listed for exclusion explicitly 
          for (UINT32 i = 0; i < numExcludeRtns; i++)
          {
            if (RTN_Name(rtn).find(_rtnExcludeKnob.Value(i)) != string::npos)
            { 
                //cerr << " excluding RTN " << RTN_Name(rtn) << std::endl;
                return false;
            } 
          }
        }

        if(numRtns)
        {
          // Some routines are listed for inclusion explicitly 
          for (UINT32 i = 0; i < numRtns; i++)
          {
            if (RTN_Name(rtn) == _rtnsKnob.Value(i))
            {
                return true;
            }
          }
        }
        else
        {
          // No explicit inclusion list hence all rtns  included
          return true;
        }

      // Some routines are listed for inclusion explicitly and this wasn't one of them
      return false;
    }

    std::string FilterKnobString()
    {
        ASSERTX(_activated);
        std::string retval="";

        UINT32 numRtns = _rtnsKnob.NumberOfValues();
        UINT32 numExcludeRtns = _rtnExcludeKnob.NumberOfValues();
        
         // No explicit inclusion or exclusion list hence all rtns  included
        if ((numRtns == 0) && (numExcludeRtns == 0))
            return retval;

        if (numExcludeRtns)
        {
          // Some routines are listed for exclusion explicitly 
          for (UINT32 i = 0; i < numExcludeRtns; i++)
          {
                retval=retval + " -filter_exclude_rtn "+_rtnExcludeKnob.Value(i);
          }
        }

        if(numRtns)
        {
          // Some routines are listed for inclusion explicitly 
          for (UINT32 i = 0; i < numRtns; i++)
          {
                retval=retval + " -filter_rtn "+_rtnsKnob.Value(i);
          }
        }
      return retval;
    }
 
  private:
    BOOL _activated;
    KNOB<string> _rtnsKnob;
    KNOB<string> _rtnExcludeKnob;
};

/*! @defgroup FILTER_MOD_LIB
  @ingroup FILTER_MOD
  Filter for selecting shared libraries
  Use -filter_no_shared_libs to ignore all shared libraries
*/

/*! @ingroup FILTER_MOD_LIB
*/
class FILTER_MOD_LIB
{
  public:
    FILTER_MOD_LIB(const string& prefix="", 
               const string& knob_family="pintool") 
        : _noSharedLibKnob(KNOB_MODE_WRITEONCE, knob_family, 
                           prefix+"filter_no_shared_libs", "", 
                           "Do not instrument shared libraries") ,
        _libExcludeKnob(KNOB_MODE_APPEND, knob_family, prefix+"filter_exclude_lib", "", 
                  "Library to NOT instrument") 
    {}

    /*! @ingroup FILTER_MOD_LIB
      Activate the filter. Must be done before PIN_StartProgram
    */
    VOID Activate()
    {}

    /*! @ingroup FILTER_MOD_LIB
      Return true if the filter is not active or the shared library that contains this trace is selected
    */
    BOOL SelectTrace(TRACE trace)
    {
        if (_noSharedLibKnob.Value()
            && (!RTN_Valid(TRACE_Rtn(trace))
                || !IMG_Valid(SEC_Img(RTN_Sec(TRACE_Rtn(trace))))
                || !IMG_IsMainExecutable(SEC_Img(RTN_Sec(TRACE_Rtn(trace)))) ))
            return false;

        UINT32 numExcludeLibs = _libExcludeKnob.NumberOfValues();
        if (numExcludeLibs)
        {
          // Some routines are listed for exclusion explicitly 
          for (UINT32 i = 0; i < numExcludeLibs; i++)
          {
            if(RTN_Valid(TRACE_Rtn(trace)) && 
               IMG_Valid(SEC_Img(RTN_Sec(TRACE_Rtn(trace)))))
            {
              string imgname = IMG_Name(SEC_Img(RTN_Sec(TRACE_Rtn(trace))));
              if(imgname.find(_libExcludeKnob.Value(i)) != string::npos)
              { 
                //cerr << " excluding lib " << imgname << std::endl;
                return false;
              } 
            }
          }
        }

        return true;
    }

    std::string FilterKnobString()
    {
        std::string retval="";

        UINT32 numExcludeLibs = _libExcludeKnob.NumberOfValues();
        if (numExcludeLibs)
        {
          // Some routines are listed for exclusion explicitly 
          for (UINT32 i = 0; i < numExcludeLibs; i++)
          {
              retval=retval + " -filter_exclude_lib "+ _libExcludeKnob.Value(i);
          }
        }

        return retval;
    }

  private:
    KNOB<BOOL> _noSharedLibKnob;
    KNOB<string> _libExcludeKnob;
};


/*! @defgroup FILTER_MOD_MULTI
  @ingroup FILTER_MOD

  Filter that includes all the filters
  See @ref FILTER_MOD_RTN, @ref FILTER_MOD_LIB
*/

/*! @ingroup FILTER_MOD_MULTI
*/
class FILTER_MOD
{
  public:

    FILTER_MOD(const string& prefix="",
           const string& knob_family="pintool") :
        _filterRtn(prefix, knob_family),
        _filterLib(prefix, knob_family)
    {}

    /*! @ingroup FILTER_MOD_MULTI
      Activate the filter. Must be done before PIN_StartProgram
    */
    VOID Activate()
    {
        _filterRtn.Activate();
        _filterLib.Activate();
    }

    /*! @ingroup FILTER_MOD_MULTI
      Return true if the filter is not active or the this trace is selected
    */
    BOOL SelectTrace(TRACE trace)
    {
        if (!_filterRtn.SelectTrace(trace)
            || !_filterLib.SelectTrace(trace)
        )
            return false;

        return true;
    }
    
    std::string FilterKnobString()
    {
      return _filterRtn.FilterKnobString()+_filterLib.FilterKnobString();
    }
    
  private:
    FILTER_MOD_RTN _filterRtn;
    FILTER_MOD_LIB _filterLib;
};

}
#endif
