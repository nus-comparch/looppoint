#!/usr/bin/env python3
# BEGIN_LEGAL
# The MIT License (MIT)
#
# Copyright (c) 2025, National University of Singapore
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# END_LEGAL

import getopt
import sys
import os
import subprocess
import glob
import bz2
import shutil
import errno
import argparse
import re
import math
import random
import hashlib
import glob
import itertools
import datetime
import tempfile
import pipes
import copy
import types

def ex(cmd, cwd = '.'):
  proc = subprocess.Popen(cmd, cwd = cwd, shell = True)
  proc.communicate()

def jobsubmit(config, files = [], out_dirs = [], startcmd = []):
  tmpdir = False
  if not config['custom_cfg']:
    target_dir = tempfile.mkdtemp()
    tmpdir = True
  else:
    target_dir = config['bm_path']
  for f in files:
    os.system('cp %s %s' % (f, target_dir))

  lp_base_dir = config['basedir']
  nthreads = config['ncores']
  program = '%(bm_suite)s-%(bm_name)s-%(bm_input)s' % config
  inputsize = config['input_class']
  wait_policy = 'PASSIVE'
  kmp_blocktime = '0'
  omp_schedule = 'STATIC'
  if 'wait_policy' in config and config['wait_policy'] == 'active':
    wait_policy = 'ACTIVE'
    kmp_blocktime = 'infinite'
  if 'schedule' in config and config['schedule'] == 'dynamic':
    omp_schedule = 'DYNAMIC'

  execute_script = r'''
ulimit -s unlimited
export OMP_STACKSIZE=192M
export KMP_BLOCKTIME=%(kmp_blocktime)s
export OMP_NUM_THREADS=%(nthreads)s
export KMP_HW_SUBSET=%(nthreads)sC,1T
export KMP_SETTINGS=true
export KMP_AFFINITY=granularity=fine,compact
export OMP_WAIT_POLICY=%(wait_policy)s
export OMP_SCHEDULE="%(omp_schedule)s"
export LD_LIBRARY_PATH=%(lp_base_dir)s/libs:$LD_LIBRARY_PATH
export PIN_APP_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
''' % locals()
  for dirname in out_dirs:
    execute_script += 'mkdir -p %s \n' % dirname
  execute_script += '''
(if [ -x "./preprocess" ]; then "./preprocess" "%(program)s" "%(inputsize)s" "%(nthreads)s" "%(lp_base_dir)s"; fi )

''' % locals()
  for i_cmd in startcmd:
    execute_script += i_cmd + '\n'
  execute_script += '''
(if [ -x "./postprocess" ]; then "./postprocess" "%(program)s" "%(inputsize)s" "%(nthreads)s" "%(lp_base_dir)s"; fi )
''' % locals()
  with open(os.path.join(target_dir, 'execute.sh'), 'w') as f:
    f.write(execute_script)
  cmd = 'bash %s' % os.path.join(target_dir, 'execute.sh')
  if config['logging']:
    os.system('echo "Running commands:" >> %s' % config['log_file'])
    for i_cmd in startcmd:
      os.system('echo "%s" >> %s' % (i_cmd, config['log_file']))
    cmd += ' 2>&1 | tee -a %s' % config['log_file']
  ex(cmd, cwd = target_dir)
  if tmpdir:
    os.system('rm -rf %s' % target_dir)
  else:
    os.system('rm -f %s' % os.path.join(target_dir, 'execute.sh'))
  return

def graphite_submit(
    config, graphiteoptions, files, traces = None, run_options = [],
    pinballs = None, startcmd = None, sniper_binary_args = None):

  tmpdir = False
  if not config['custom_cfg']:
    target_dir = tempfile.mkdtemp()
    tmpdir = True
  else:
    target_dir = config['bm_path']

  for f in files:
    os.system('cp %s %s' % (f, target_dir))

  run_options = ' '.join(run_options)
  lp_base_dir = config['basedir']
  sniper_root = config['sniper_root']
  nthreads = int(config['ncores'])
  program = '%(bm_suite)s-%(bm_name)s-%(bm_input)s' % config
  inputsize = config['input_class']
  wait_policy = 'PASSIVE'
  kmp_blocktime = '0'
  omp_schedule = 'STATIC'
  if 'wait_policy' in config and config['wait_policy'] == 'active':
    wait_policy = 'ACTIVE'
    kmp_blocktime = 'infinite'
  if 'schedule' in config and config['schedule'] == 'dynamic':
    omp_schedule = 'DYNAMIC'
  if sniper_binary_args:
    sniper_binary_args = ' '.join(['--', sniper_binary_args] )

  graphite_extra_opts = '''      -n %(nthreads)u \
      %(graphiteoptions)s \
       %(sniper_binary_args)s''' % locals()

  if startcmd:
    postprocess = None
    graphite_extra_opts = ''
  elif traces:
    startcmd = '$GRAPHITE_ROOT/run-sniper --traces=%(traces)s %(run_options)s' % locals()
  elif pinballs:
    startcmd = '$GRAPHITE_ROOT/run-sniper --pinballs=%(pinballs)s %(run_options)s' % locals()
  elif sniper_binary_args:
    startcmd = '$GRAPHITE_ROOT/run-sniper %(run_options)s' % locals()
  else:
    return

  with open(os.path.join(target_dir, 'execute.sh'), 'w') as f:
    f.write(r'''
    export GRAPHITE_ROOT=%(sniper_root)s
    export SNIPER_ROOT=%(sniper_root)s

    ulimit -s unlimited
    export OMP_STACKSIZE=192M
    export KMP_BLOCKTIME=%(kmp_blocktime)s
    export OMP_NUM_THREADS=%(nthreads)s
    export KMP_HW_SUBSET=%(nthreads)sC,1T
    export KMP_SETTINGS=true
    export KMP_AFFINITY=granularity=fine,compact
    export OMP_WAIT_POLICY=%(wait_policy)s
    export OMP_SCHEDULE="%(omp_schedule)s"
    export LD_LIBRARY_PATH=%(lp_base_dir)s/libs:$LD_LIBRARY_PATH
    export SNIPER_SIM_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
    export SNIPER_APP_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
    export PIN_APP_LD_LIBRARY_PATH=$LD_LIBRARY_PATH

    (if [ -x "./preprocess" ]; then "./preprocess" "%(program)s" "%(inputsize)s" "%(nthreads)s" "%(lp_base_dir)s"; fi )
    %(startcmd)s \
      %(graphite_extra_opts)s
    (if [ -x "./postprocess" ]; then "./postprocess" "%(program)s" "%(inputsize)s" "%(nthreads)s" "%(lp_base_dir)s"; fi )
    ''' % locals())

  cmd = 'bash %s' % os.path.join(target_dir, 'execute.sh')
  if config['logging']:
    os.system('echo "Running command:" >> %s' % config['log_file'])
    os.system('echo "%s %s" >> %s' % (startcmd, graphite_extra_opts, config['log_file']))
    cmd += ' 2>&1 | tee -a %s' % config['log_file']
  ex(cmd, cwd = target_dir)
  if tmpdir:
    os.system('rm -rf %s' % target_dir)
  else:
    os.system('rm -f %s' % os.path.join(target_dir, 'execute.sh'))
  return

