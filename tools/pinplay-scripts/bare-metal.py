#!/usr/bin/env python3
'''
#BEGIN_LEGAL 
INTEL CONFIDENTIAL

Copyright (c) 2004-2018, Intel Corporation. All rights reserved.

The source code contained or described herein and all documents
related to the source code ("Material") are owned by Intel Corporation
or its suppliers or licensors. Title to the Material remains with
Intel Corporation or its suppliers and licensors. The Material
contains trade secrets and proprietary and confidential information of
Intel or its suppliers and licensors. The Material is protected by
worldwide copyright and trade secret laws and treaty provisions. No
part of the Material may be used, copied, reproduced, modified,
published, uploaded, posted, transmitted, distributed, or disclosed in
any way without Intel's prior express written permission.

No license under any patent, copyright, trade secret or other
intellectual property right is granted to or conferred upon you by
disclosure or delivery of the Materials, either expressly, by
implication, inducement, estoppel or otherwise. Any license under such
intellectual property rights must be express and approved by Intel in
writing.

END_LEGAL
'''
#
#
# @ORIGINAL_AUTHORS: Michael Gorin
#
#

import sys
import os
import random
import subprocess
import optparse
import xml.etree.ElementTree as xml

# Local modules
#
import cmd_options
import config
import kit
import msg
import util

class Bare(object):
    """
    Generate bare metal object files for an silicon
    """

    def GetKit(self):
        """
        Get the PinPlay kit.

        @return PinPlay kit
        """
        return kit.Kit()

    """ Prints a message with a fixed prefix"""
    def PrintMsg(self,msg):
        print('Bare metal: '+msg)

    """ Prints an error message and exit """
    def PrintAndExit(self,msg):
        self.PrintMsg(msg)
        sys.exit(-1)

    """ Prints an error message with help and exit """
    def PrintHelpAndExit(self,msg):
        self.PrintMsg(msg + '. Use bare-metal.py --help to see valid argument options.')
        sys.exit(-1)    

    def ParseCommandLine(self):
        """
        Parse command line arguments and check to make sure all required options were given.

        @return List of options
        """

        ## command line options for the bare metal   
        parser = optparse.OptionParser()
        
        ## command line arguments to bare metal script
        parser.add_option("--lit", dest="lit",
                  default="", 
                  help="LIT trace to convert to bare metal")
        
        parser.add_option("--archsim", dest="archsim",
                  default="", 
                  help="archsim binary location")
                          
        parser.add_option("--output", dest="output",
                  default="baremetal", 
                  help="Bare metal output file name")     
                  
        ## command line arguments to control script behavior
        parser.add_option("-v", "--verbose", dest="verbose",
                  action="store_true", default=False,
                  help="Print out command line used and other information")                  
    
        (options, args) = parser.parse_args()

        ## Check options validity 
        if ( options.lit == "" ):
            self.PrintAndExit("Lit name cannot be empty")   
        if ( options.archsim == "" ):
            self.PrintAndExit("archsim binary location cannot be empty")     
        if ( options.output == "" ):
            self.PrintAndExit("Bare metal output file name cannot be empty")    
        if ( options.verbose ):
            self.verbose = "-v"
        else:
            self.verbose = ""            
                        
        return options         

    def run_litup(self):
        """
        Run LitUp script 
        """   
        # LitUp is non-sde source with unsupported python shebang-line.
        # invoke LitUp.py with the same interpreter that run bare-metal.py
        py_inter = '{} '.format(sys.executable)

        cmd = py_inter + \
              os.path.join(os.path.dirname(os.path.realpath(__file__)),'LitUp.py') + \
              ' --ami ' + self.ami_file + ' --arch-xml ' + self.xml_file + \
              ' --output ' + self.output + ' ' + self.verbose + \
              ' --iasm "' + self.archsim + ' -asm -b all -32 -max_addr 52 -no_obj" '
        result = util.RunCmd(cmd,None,'')
        if result != 0:
            self.PrintAndExit("fail on cmd: {}".format(cmd))

    def Run(self):
        """
        Get all the user options and run the bare metal creator.

        @return Exit code for the creation
        """
        
        # Get command line options
        options = self.ParseCommandLine()

        # Check files
        self.ami_file = options.lit+'.ami'    
        if not os.path.exists(self.ami_file):
            self.PrintAndExit("Ami file does not exist ")       
        self.xml_file = options.lit+'.arch.xml'    
        if not os.path.exists(self.xml_file):
            self.PrintAndExit("Xml file does not exist ")      
        self.archsim = os.path.join(options.archsim,'archsim')    
        if not os.path.exists(self.archsim):
            self.PrintAndExit("archsim binary not exist ")                  
        self.output = options.output

        # Get the kit to be used for bare metal.
        #
        #kit = self.GetKit()
        
        # Run LitUp script
        self.run_litup()        
                 
def main():
    """
       This method allows the script to be run in stand alone mode.

       @return Exit code from running the script
       """

    bare = Bare()
    result = bare.Run()
    return result

# If module is called in stand along mode, then run it.
#
if __name__ == "__main__":
    result = main()
    sys.exit(result)