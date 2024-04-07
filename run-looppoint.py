#!/usr/bin/env python2
# BEGIN_LEGAL
# The MIT License (MIT)
#
# Copyright (c) 2022, National University of Singapore
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

from __future__ import division
import getopt, sys, os, subprocess, glob, bz2, shutil
import time, errno, ConfigParser
from tabulate import tabulate
import lplib
if not os.path.isdir(os.path.join(os.path.dirname(__file__), 'tools', 'sniper')):
  print ('[LOOPPOINT] Error: Sniper not found.')
  exit(1)
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools', 'sniper', 'tools'))
import sniper_lib, cpistack

def ex(cmd, cwd='.'):
  proc = subprocess.Popen([ 'bash', '-c', cmd ], cwd=cwd)
  proc.communicate()

def ex_log(cmd, config, cwd='.', logging=True):
  print ('[command] %s' % cmd)
  if logging:
    cmd += ' 2>&1 | tee -a %(log_file)s' % config
  ex(cmd, cwd)

def log(config, *args):
  fun = sys._getframe(1).f_code.co_name
  ex_log('echo "[%s()] %s"' % (fun, ' '.join(map(str, args))), config)

def ex_env(cmd, config, env, cwd='.', logging=True):
  print ('[command] %s' % cmd)
  if logging:
    cmd += ' 2>&1 | tee -a %(log_file)s' % config
  proc = subprocess.Popen(cmd, env=env, cwd=cwd, shell=True)
  proc.communicate()

def ex_res(cmd, config, env, cwd='.', logging=True):
  print ('[command] %s' % cmd)
  if logging:
    cmd += ' 2>&1 | tee -a %(log_file)s' % config
  proc = subprocess.Popen(cmd, env=env, cwd=cwd, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
  output=proc.stdout.read()
  return output

def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else:
      raise

def get_app_cmd(config):
  configParser = ConfigParser.ConfigParser()
  configParser.read(config['app_cfg'])
  binary_args = configParser.get('Parameters','command').split('>')[0]
  return binary_args

def make_mt_pinball(config):
  mkdir_p(os.path.dirname(config['whole_basename']))
  print ("[LOOPPOINT] Generating fat pinball.")
  files = []
  if not config['custom_cfg']:
    files.append('preprocess')
  out_dirs = []
  cmd = '%(tool_sde_pinpoints)s --delete --mode mt --sdehome=%(sde_kit)s ' % config
  if config['use_pinplay']:
    cmd = '%(tool_pinpoints)s --delete --mode mt --pintool="%(pintool_looppoint)s" ' % config
  cmd += ' --cfg %(app_cfg)s --log_options "' % config + ('-log:start_address' if config['use_pinplay'] else '-start_address') + ' main -log:fat  -log:mp_atomic 0 -log:mp_mode 0 -log:strace -log:basename %(whole_basename)s" --replay_options="-replay:strace" -l' % config
  lplib.jobsubmit(config, files = files, out_dirs = out_dirs, startcmd = [cmd])

def gen_dcfg(config):
  print ("[LOOPPOINT] Generating DCFG file.")
  if config['use_pinplay'] and not os.path.isfile(config['pintool_looppoint']):
    print ("[LOOPPOINT] Error: LoopPoint tool not found.")
    exit(1)
  if not config['binary_profile']:
    wpp_name = glob.glob(config['whole_basename'] + '*.address')
    if not wpp_name:
      print ("[LOOPPOINT] Error: Whole-program pinball not found.")
      exit(1)
    wpp_basename = wpp_name[-1].rsplit('.', 1)[0]
    update_config = {}
    update_config['wpp_basename'] = wpp_basename
    update_config['wpp_dir'] = update_config['wpp_basename'].rsplit('/', 1)[0]
    config.update(update_config)
  files = []
  outdirs = []

  if not config['binary_profile']:
    cmd = '%(sdetool_replay)s --pintool=%(sdetool_dcfg)s ' % config
    if config['use_pinplay']:
      cmd = '%(tool_replay)s --pintool=%(pintool_looppoint)s ' % config
    cmd += ' --pintool_options "-dcfg -replay:deadlock_timeout 0 -replay:strace -dcfg:out_base_name %(wpp_basename)s" %(wpp_basename)s' % config
  else:
    if not config['custom_cfg']:
      files.append('preprocess')
    update_config = {}
    update_config['wpp_dir'] = os.path.dirname(config['whole_basename'])
    config.update(update_config)
    mkdir_p(config['wpp_dir'])
    cmd = '%(sde64)s -t %(sdetool_looppoint)s -dcfg -dcfg:out_base_name %(wpp_dir)s/dcfg-out -- ' % config
    cmd += get_app_cmd(config)

  print ("[LOOPPOINT] Running cmd %s" %cmd)
  lplib.jobsubmit(config, files = files, out_dirs = outdirs, startcmd = [cmd])

def gen_bbv(config):
  print ("[LOOPPOINT] Profiling for BBV Generation.")
  dcfg_file = glob.glob(config['wpp_dir'] + '/*.dcfg.json.bz2')
  if not dcfg_file:
    print ("[LOOPPOINT] Error: DCFG file not found.")
    exit(1)
  config['dcfg_file'] = dcfg_file[-1]
  files = []
  outdirs = []

  if not config['binary_profile']:
    cmd = '%(tool_sde_pinpoints)s --pintool="%(sdetool_looppoint)s" --sdehome=%(sde_kit)s ' % config
    if config['use_pinplay']:
      cmd = '%(tool_pinpoints)s --pintool="%(pintool_looppoint)s" ' % config

    cmd += ' --global_regions --pccount_regions --cfg %(app_cfg)s --whole_pgm_dir %(wpp_dir)s --mode mt -S %(slice_size)s -b --replay_options "-replay:deadlock_timeout 0 -global_profile -emit_vectors 0 -filter_exclude_lib libgomp.so.1 -filter_exclude_lib libiomp5.so  -looppoint:global_profile -looppoint:dcfg-file %(dcfg_file)s -looppoint:main_image_only 1 -looppoint:loop_info %(bm_name)s.%(bm_input)s.loop_info.txt' % config
    if config['flowcontrol']:
      cmd += ' -flowcontrol:verbose 1 -flowcontrol:quantum 1000000 -flowcontrol:maxthreads %(ncores)s' % config
    cmd += '"'
    ex_log(cmd, config, cwd = config['output_base_dir'])
  else:
    if not config['custom_cfg']:
      files.append('preprocess')
    data_dir = os.path.join(config['output_base_dir'], '%(bm_name)s.%(bm_input)s_%(pid)s.Data' % config)
    mkdir_p(data_dir)
    config['data_dir'] = data_dir
    cmd = '%(sde64)s  -t %(sdetool_looppoint)s  -global_profile -emit_vectors 0 -filter_exclude_lib libgomp.so.1 -filter_exclude_lib libiomp5.so  -looppoint:global_profile -looppoint:dcfg-file %(dcfg_file)s -looppoint:main_image_only 1 -looppoint:loop_info %(bm_name)s.%(bm_input)s.loop_info.txt -bbprofile -slice_size %(slice_size)s -o  %(data_dir)s/%(bm_name)s.%(bm_input)s_%(pid)s -log:mt 1' % config
    if config['flowcontrol']:
      cmd += ' -flowcontrol:verbose 1 -flowcontrol:quantum 1000000 -flowcontrol:maxthreads %(ncores)s' % config
    cmd += ' -- %s' % (get_app_cmd(config))
    print ("[LOOPPOINT] Running cmd %s" %cmd)
    lplib.jobsubmit(config, files = files, out_dirs = outdirs, startcmd = [cmd])

  # Concatenation of BBVs
  data_dir = glob.glob(config['output_base_dir'] + '/*.Data')
  if not data_dir:
    print ("[LOOPPOINT] Error: Profile data not found.")
    exit(1)
  config['data_dir'] = data_dir[0]
  globalbb = glob.glob(config['data_dir'] + '/*.global.bb*')
  if not globalbb:
    print ("[LOOPPOINT] Error: Global BBV not found.")
    exit(1)
  bb_basename = os.path.join(config['data_dir'], config['data_dir'].split('/')[-1].rsplit('.', 1)[0])
  config['bb_basename'] = bb_basename
  if not config['force']:
    cvfile = glob.glob(config['data_dir'] + '/*.global.cv')
    if cvfile:
      print ("[LOOPPOINT] Found concatenated vector. Not generating.")
      return
  cmd = '%(tool_concat_vector)s %(bb_basename)s %(ncores)s' % config
  ex_log(cmd, config)
  try:
    cvfile = glob.glob(config['data_dir'] + '/*.global.cv')[0]
  except:
    print('[LOOPPOINT] Error: Concatenated vector not generated. Using global (all threads) vector.')
  globalbbname = cvfile.replace('.cv', '.bb')
  print(globalbbname)
  if os.path.islink(globalbbname):
    os.remove(globalbbname)
  elif os.path.isfile(globalbbname):
    os.rename(globalbbname, globalbbname + '.bkp')
  curr_cwd = os.getcwd()
  os.chdir(config['data_dir'])
  print(cvfile.split('/')[-1], globalbbname.split('/')[-1])
  os.symlink(cvfile.split('/')[-1], globalbbname.split('/')[-1])
  os.chdir(curr_cwd)
  return

def gen_cluster(config):
  print ("[LOOPPOINT] Clustering the BBVs.")
  if not config['binary_profile']:
    cmd = '%(tool_sde_pinpoints)s --pintool="sde-global-looppoint.so" ' % config
    if config['use_pinplay']:
      cmd = '%(tool_pinpoints)s ' % config
    cmd += ' --global_regions --pccount_regions --cfg %(app_cfg)s --whole_pgm_dir %(wpp_dir)s -S %(slice_size)s --warmup_factor=%(warmup_factor)s --maxk=%(cluster_maxk)s --dimensions=%(cluster_dim)s --append_status -s' % config
    cmd += ' --simpoint_options="'
    if config['cluster_dim']:
      cmd += ' -dim %(cluster_dim)s' % config
    if config['cluster_maxk']:
      cmd += ' -coveragePct 1.0 -maxK %(cluster_maxk)s '% config
    cmd += '"'
    ex_log(cmd, config, cwd = config['output_base_dir'])
  else:
    cmd1 = '%(sde_pinplay)s/PinPointsHome/Linux/bin/simpoint -loadFVFile %(bb_basename)s.global.bb -saveSimpoints %(data_dir)s/t.simpoints -saveSimpointWeights %(data_dir)s/t.weights -saveLabels %(data_dir)s/t.labels -verbose 1' % config
    if config['cluster_dim']:
      cmd1 += ' -dim %(cluster_dim)s' % config
    if config['cluster_maxk']:
      cmd1 += ' -coveragePct 1.0 -maxK %(cluster_maxk)s '% config
    env = os.environ.copy()
    simpt_path = os.path.join(config['sde_pinplay'], 'PinPointsHome/Linux/bin')
    env['PATH'] = '%s:%s:%s'%(simpt_path, config['sde_pinplay'], env['PATH'])
    ex_env(cmd1, config, env, cwd = config['output_base_dir'])
    cmd2 = '%(sde_pinplay)s/pcregions.py  --warmup_factor %(warmup_factor)s --tid global --bbv_file %(bb_basename)s.global.bb --region_file %(data_dir)s/t.simpoints --weight_file %(data_dir)s/t.weights --label_file %(data_dir)s/t.labels' % config
    csv_content = ex_res(cmd2, config, env, cwd = config['output_base_dir'])
    csvfile = open ('%(bb_basename)s.global.pinpoints.csv' % config, 'w+')
    csvfile.write(csv_content)

def get_address_pccount(line, wd):
  csv_entries = line.split(',')
  if wd == 'start':
    return csv_entries[3], csv_entries[6]
  elif wd == 'end':
    return csv_entries[7], csv_entries[10]
  return None, None

def get_image_offset(line, wd):
  csv_entries = line.split(',')
  if wd == 'start':
    return csv_entries[4], csv_entries[5]
  elif wd == 'end':
    return csv_entries[8], csv_entries[9]
  return None, None

def get_regionid(line):
  regionid = line.split(',')[2]
  return regionid

def get_multiplier(line):
  multiplier = line.split(',')[14]
  return float(multiplier)

def get_startsim_parms(sim_config, config):
  sniper_args = []
  sniper_args += ['-v']
  sniper_args += ['-sprogresstrace:10000000']
  sniper_args += ['-gtraceinput/timeout=2000']
  sniper_args += ['-gscheduler/type=%(scheduler)s' % sim_config]
  sniper_args += ['-c%(arch_cfg)s' % sim_config]
  sniper_args += ['--trace-args="-sniper:flow 1000"']
  if  ('end_address' in sim_config) and (sim_config['end_address'] != None):
    if sim_config['start_address_count'] == '0':
      sniper_args += ['-ssimuserroi --roi-script --trace-args="%(controller)s stop:address:%(end_image)s+%(end_offset)s:count%(end_address_count)s:global"' % sim_config]
    else:
      sniper_args += ['-ssimuserroi --roi-script --trace-args="%(controller)s start:address:%(start_image)s+%(start_offset)s:count%(start_address_count)s:global" --trace-args="%(controller)s stop:address:%(end_image)s+%(end_offset)s:count%(end_address_count)s:global"' % sim_config]
    sniper_args += ['-gperf_model/fast_forward/oneipc/interval=100']
    sniper_args += ['-ggeneral/inst_mode_init=detailed']
  if ('rob_config' in sim_config) and (sim_config['rob_config'] == True):
    sniper_args += ['-c rob']
  if ('dram_perf_qmodel' in sim_config) and (sim_config['dram_perf_qmodel'] == False):
    sniper_args += ['-gperf_model/dram/queue_model/enabled=false']
  if ('include_mem_latency' in sim_config) and (sim_config['include_mem_latency'] == True):
    sniper_args += ['-gperf_model/fast_forward/oneipc/include_memory_latency=true']
  if ('viz' in sim_config) and (sim_config['viz'] == True):
    sniper_args += ['--viz']
  if ('regionid' in sim_config) and (sim_config['regionid'] != None):
    sniper_args += ['-d %s' % os.path.join(config['sim_res_dir'], sim_config['regionid'])]
  return sniper_args

def run_sniper(config, mtng=True):
  print ("[LOOPPOINT] Starting Sniper simulations")
  arch_cfg = 'gainestown'
  scheduler = 'static'
  sniper_binary_args = None
  configParser = ConfigParser.ConfigParser()
  configParser.read(config['app_cfg'])
  sniper_binary_args = '"' + configParser.get('Parameters','command').split('>')[0] + '"'
  include_mem_latency = True
  rob_config = False
  dram_perf_qmodel = None
  viz = False
  files = []
  if not config['custom_cfg']:
    files.append('preprocess')
  traces = None
  run_options = []
  pinballs = None
  startcmd = None
  if config['validate'] and not config['reuse_fullsim']:
    wp_config = {}
    wp_config['arch_cfg'] = arch_cfg
    wp_config['scheduler'] = scheduler
    wp_config['sniper_binary_args'] = sniper_binary_args
    wp_config['regionid'] = 'wp'
    wp_config['include_mem_latency'] = include_mem_latency
    wp_config['rob_config'] = rob_config
    wp_config['dram_perf_qmodel'] = dram_perf_qmodel
    wp_config['include_mem_latency'] = include_mem_latency
    wp_config['viz'] = viz
    flags = get_startsim_parms(wp_config, config)
    graphiteoptions = ''
    if flags:
      graphiteoptions += ' ' + ' '.join(flags)

    lplib.graphite_submit(config, graphiteoptions, files, traces = traces, run_options = run_options, pinballs = pinballs, startcmd = startcmd, sniper_binary_args = sniper_binary_args)

  csv_file = glob.glob(config['data_dir'] + '/*.global.pinpoints.csv')
  if not csv_file:
    print ("[LOOPPOINT] Error: Unable to find cluster information.")
  with open(csv_file[0], 'r') as f:
    for csv_line in f:
      if not csv_line.startswith('cluster'):
        continue
      start_address = None
      start_address_count = '0'
      end_address = None
      end_address_count = '0'
      regionid = None
      regionid = get_regionid(csv_line)

      start_address, start_address_count = get_address_pccount(csv_line, 'start')
      start_image, start_offset = get_image_offset(csv_line, 'start')
      end_address, end_address_count = get_address_pccount(csv_line, 'end')
      end_image, end_offset = get_image_offset(csv_line, 'end')
      rep_config = {}
      rep_config['arch_cfg'] = arch_cfg
      rep_config['scheduler'] = scheduler
      rep_config['start_address'] = start_address
      rep_config['start_image'] = start_image
      rep_config['start_offset'] = start_offset
      rep_config['start_address_count'] = start_address_count
      rep_config['end_address'] = end_address
      rep_config['end_image'] = end_image
      rep_config['end_offset'] = end_offset
      rep_config['end_address_count'] = end_address_count
      rep_config['sniper_binary_args'] = sniper_binary_args
      rep_config['regionid'] = 'r%s' % regionid
      rep_config['include_mem_latency'] = include_mem_latency
      rep_config['rob_config'] = rob_config
      rep_config['dram_perf_qmodel'] = dram_perf_qmodel
      rep_config['include_mem_latency'] = include_mem_latency
      rep_config['viz'] = viz
      rep_config['controller'] = '-control' if config['sniper_sde'] else '-pinplay:control'
      flags = get_startsim_parms(rep_config, config)
      graphiteoptions = ''
      if flags:
        graphiteoptions += ' ' + ' '.join(flags)

      lplib.graphite_submit(config, graphiteoptions, files, traces = traces, run_options = run_options, pinballs = pinballs, startcmd = startcmd, sniper_binary_args = sniper_binary_args)

def get_sim_res(config, sim_path, profile_path, region = None):
  if region == None:
    return -1
  resultsdir = os.path.join(sim_path, region)
  try:
    res = sniper_lib.get_results(resultsdir=resultsdir)
  except (KeyError, ValueError), e:
    print('[LOOPPOINT] Error: Unable to fetch results for %s.' % region)
    if region == 'wp':
      exit(1)
    return -1
  results = res['results']
  config = res['config']
  return results, config

def read_simstats(results, config, param, coreid = -1):
  ncores = int(config['general/total_cores'])
  if param == 'runtime':
    if 'barrier.global_time_begin' in results:
      time0_begin = results['barrier.global_time_begin']
      time0_end = results['barrier.global_time_end']
    if 'barrier.global_time' in results:
      time0 = results['barrier.global_time'][0]
    else:
      time0 = time0_begin - time0_end
    time_ns = (lambda x: (x/1e6))(time0)
    return time_ns
  if param == 'instructions':
    if sum(results['performance_model.instruction_count']) == 0:
      results['performance_model.instruction_count'] = results['core.instructions']
    if coreid >= 0 and coreid < ncores:
      return results['performance_model.instruction_count'][coreid]
    else:
      return sum(results['performance_model.instruction_count'])
  return -1


def evaluate(config):
  print('[LOOPPOINT] Collecting results for %(bm_fullname)s.%(bm_input)s using %(input_class)s input class and %(wait_policy)s OMP wait policy' % config)
  sim_path = ''
  profile_path = ''
  if config['force']:
    if config['reuse_fullsim']:
      sim_path = config['sim_res_dir']
      profile_path = config['data_dir']
    if config['reuse_profile']:
      sim_path = config['sim_res_dir']
      try:
        profile_path = glob.glob(config['output_base_dir_default'] + '/*.Data')[0]
      except:
        print('[LOOPPOINT] Error: Could not find profile directory.')
        exit(1)
    else:
      sim_path = config['sim_res_dir']
      profile_path = config['data_dir']
  else:
    sim_path = config['sim_res_dir_default']
    try:
      profile_path = glob.glob(config['output_base_dir_default'] + '/*.Data')[0]
    except:
      print('[LOOPPOINT] Error: Could not find profile directory.')
      exit(1)
  region_stats = {}
  region_config = {}
  region_mult = {}
  if config['validate']:
    region_stats['wp'], region_config['wp'] = get_sim_res(config, config['sim_res_dir_default'] if config['reuse_fullsim'] else sim_path, profile_path, 'wp')
  csv_file = glob.glob(profile_path + '/*.global.pinpoints.csv')
  if not csv_file:
    print('[LOOPPOINT] Error: Unable to find cluster information.')
  with open(csv_file[0], 'r') as f:
    for csv_line in f:
      if not csv_line.startswith('cluster'):
        continue
      regionid = get_regionid(csv_line)
      multiplier = get_multiplier(csv_line)
      region_mult[regionid] = multiplier
      try:
        region_stats[regionid], region_config[regionid] = get_sim_res(config, sim_path, profile_path, 'r%s' % regionid)
      except:
        print('[LOOPPOINT] Error: Simulation results not found for r%s' % regionid)

  extrapolated_runtime = 0.0
  max_rep_runtime = 0.0
  sum_rep_runtime = 0.0
  cov_mult = 0.0
  tot_mult = sum(region_mult.values())
  for regionid, multiplier in region_mult.iteritems():
    region_runtime = 0
    try:
      region_runtime =  read_simstats(region_stats[regionid], region_config[regionid], 'runtime')
    except:
      print('[LOOPPOINT] Warning: Skipping r%s as the simulation results are not available' % regionid)
      continue
    cov_mult += multiplier
    extrapolated_runtime += region_runtime * multiplier
    if region_runtime > max_rep_runtime:
      max_rep_runtime = region_runtime
    sum_rep_runtime += region_runtime

  coverage = cov_mult/tot_mult
  extrapolated_runtime = extrapolated_runtime/coverage

  if config['validate']:
    full_prog_runtime = read_simstats(region_stats['wp'], region_config['wp'], 'runtime')
    speedup_p = full_prog_runtime/max_rep_runtime
    speedup_s = full_prog_runtime/(sum_rep_runtime/coverage)

  if config['validate']:
    tab = [ '%(bm_fullname)s.%(bm_input)s' % config, round(full_prog_runtime, 2), round(extrapolated_runtime, 2), round((1-(extrapolated_runtime/full_prog_runtime))*100, 2), round(speedup_p, 2), round(speedup_s, 2), round(coverage*100, 2) ]
  else:
    tab = [ '%(bm_fullname)s.%(bm_input)s' % config, round(extrapolated_runtime, 2), round(coverage*100, 2) ]
  return tab

def run_native(config):
  print ('[LOOPPOINT] Running %(bm_fullname)s.%(bm_input)s natively using %(input_class)s input class and %(wait_policy)s OMP wait policy' % config)
  files = ['preprocess']
  out_dirs = []
  #cmd = 'perf stat -e instructions:u %s' % get_app_cmd(config)
  cmd = '%s' % get_app_cmd(config)
  lplib.jobsubmit(config, files = files, out_dirs = out_dirs, startcmd = [cmd])
  return

def bm_to_path(config):
  name_to_dir = {
    'bwaves': '603.bwaves_s',
    'cactus': '607.cactuBSSN_s',
    'lbm': '619.lbm_s',
    'wrf': '621.wrf_s',
    'cam4': '627.cam4_s',
    'pop2': '628.pop2_s',
    'imagick': '638.imagick_s',
    'nab': '644.nab_s',
    'fotonik': '649.fotonik3d_s',
    'roms': '654.roms_s',
    'xz': '657.xz_s',
    'matrix': 'matrix-omp',
    'dijkstra': 'dijkstra-openmp',
    'dotproduct': 'dotproduct-omp',
    'bt': 'bt',
    'cg': 'cg',
    'ep': 'ep',
    'ft': 'ft',
    'is': 'is',
    'lu': 'lu',
    'mg': 'mg',
    'sp': 'sp',
    'ua': 'ua',
  }
  config['bm_fullname'] = name_to_dir[config['bm_name']]
  config['bm_path'] = os.path.join(config['app_base'], config['bm_suite'], config['bm_fullname'])
  if config['bm_suite'] == 'npb':
    if config['input_class'] == 'train':
      config['input_class'] = 'C'
    elif config['input_class'] == 'test':
      config['input_class'] = 'A'
  cfg_file = glob.glob(config['bm_path'] + '/' + config['input_class'] + '/' + config['bm_fullname'] + '.' + config['bm_input'] + '.cfg')
  if not cfg_file:
    print ('[LOOPPOINT] Error: Invalid config or config file not found.')
    exit(1)
  config['app_cfg'] = cfg_file[0]
  return

def bm_custom_dir(config):
  config['app_cfg'] = config['custom_cfg']
  configParser = ConfigParser.ConfigParser()
  configParser.read(config['app_cfg'])
  config['bm_name'] = configParser.get('Parameters', 'program_name')
  config['bm_path'] = config['app_cfg'].rsplit('/', 1)[0]
  config['bm_suite'] = 'custom'
  config['bm_fullname'] = config['bm_name']
  config['bm_input'] = configParser.get('Parameters', 'input_name')
  return

def add_dependent_config(config):
  if not config['custom_cfg']:
    bm_to_path(config)
  else:
    bm_custom_dir(config)
  config['bm_param_str'] = '-'.join([ config['bm_suite'], config['bm_name'], config['bm_input'], config['input_class'], config['wait_policy'], config['ncores'] ])
  # output dirs
  if not config['custom_cfg']:
    config['output_base_dir_default'] = os.path.join(config['basedir'],'results', config['bm_param_str'] + '-default')
    config['output_base_dir'] = os.path.join(config['basedir'],'results', config['bm_param_str'] + '-' + time.strftime("%Y%m%d%H%M%S"))
  else:
    config['output_base_dir_default'] = os.path.join(config['bm_path'], config['bm_param_str'] + '-default')
    config['output_base_dir'] = os.path.join(config['bm_path'], config['bm_param_str'] + '-' + time.strftime("%Y%m%d%H%M%S"))

  config['sim_res_dir_default']  = os.path.join(config['output_base_dir_default'],'simulation')
  config['sim_res_dir']  = os.path.join(config['output_base_dir'],'simulation')
  config['whole_basename'] = os.path.join(config['output_base_dir'], 'whole_program.' + config['bm_input'], config['bm_name'] + '.' + config['bm_input'])
  # regions of size 100M instructions per thread for regular applications and 10M per thread for demo applications
  config['slice_size'] = str(int(config['ncores'])*10000000) if config['bm_suite'] == 'demo' else str(int(config['ncores'])*100000000)
  if config['bm_suite'] == 'demo':
    config['cluster_maxk'] = '20'

  # logging
  config['log_file'] = os.path.join(os.path.join(config['output_base_dir'], 'looppoint.log.txt'))
  config['logging'] = True
  return

def create_default_config():
  config = {}

  # application
  config['bm_name'] = 'matrix'
  config['bm_suite'] = 'demo'
  config['bm_input'] = '1'
  config['input_class'] = 'test'
  config['wait_policy'] = 'passive'
  config['schedule'] = 'static'

  # directories
  config['basedir'] = os.path.dirname(os.path.realpath(__file__))

  # cluster parameters
  config['warmup_factor'] = '2'
  config['cluster_dim']  = '100'
  config['cluster_maxk']   = '50'

  # tools
  config['app_base'] = os.path.join(config['basedir'], 'apps')
  config['tools_base'] = os.path.join(config['basedir'], 'tools')
  config['pin_kit'] =  os.path.join(config['tools_base'], 'pin-3.13-98189-g60a6ef199-gcc-linux')
  config['sde_kit'] =  os.path.join(config['tools_base'], 'sde-external-9.14.0-2022-10-25-lin')
  config['sde64'] =  os.path.join(config['sde_kit'], 'sde64')
  config['sniper_root'] = os.path.join(config['tools_base'], 'sniper')
  config['pinplay'] = os.path.join(config['pin_kit'], 'extras', 'pinplay')
  config['sde_pinplay'] = os.path.join(config['sde_kit'], 'pinplay-scripts')
  config['pintool_looppoint'] = os.path.join(config['pinplay'], 'bin/intel64/global_looppoint.so')
  config['sdetool_looppoint'] = 'sde-global-looppoint.so'
  config['tool_pinpoints'] = os.path.join(config['pinplay'], 'scripts/pinpoints.py')
  config['tool_sde_pinpoints'] = os.path.join(config['sde_pinplay'], 'sde_pinpoints.py')
  config['tool_replay'] = os.path.join(config['pinplay'], 'scripts/replay.py')
  config['tool_concat_vector'] = os.path.join(config['basedir'], 'tools', 'gen-concat-vectors')
  config['sdetool_replay'] = os.path.join(config['sde_kit'], 'pinplay-scripts/replay.py')
  config['sdetool_dcfg'] = 'sde-global-looppoint.so'

  # other config
  config['pin_options'] = '-xyzzy '
  config['force'] = False
  config['reuse_profile'] = False
  config['reuse_fullsim'] = False
  config['validate'] = True
  config['use_pinplay'] = False
  config['sniper_sde'] = False
  config['binary_profile'] = False

  # Number of cores
  config['ncores'] = os.getenv('OMP_NUM_THREADS', '8')

  config['flowcontrol'] = True
  config['custom_cfg'] = ''
  config['native_run'] = False
  config['pid'] = str(os.getpid())

  return config

def check_dep(config):
  if config['use_pinplay'] and not os.path.exists(config['pin_kit']):
    print ("Error detected while finding Pin kit. Double check these paths!")
    sys.exit(1)
  if not (config['use_pinplay'] or os.path.exists(config['sde_kit'])):
    print ("Error detected while finding SDE kit. Double check these paths!")
    sys.exit(1)
  if not os.path.exists(config['sniper_root']):
    print("Error detected while finding Sniper. Double check these paths!")
    sys.exit(1)
  if config['use_pinplay'] and not os.path.isfile(os.path.join(config['pin_kit'],'pin')):
    raise RuntimeError('Cannot find Pin kit at [%s]' % config['pin_kit'])
  if not (config['use_pinplay'] or os.path.isfile(os.path.join(config['sde_kit'],'sde'))):
    raise RuntimeError('Cannot find SDE kit at [%s]' % config['sde_kit'])
  if not os.path.isfile(os.path.join(config['sniper_root'],'run-sniper')):
    raise RuntimeError('Cannot find Sniper at [%s]' % config['sniper_root'])
  if not os.path.isfile(os.path.join(config['sniper_root'],'lib', 'sniper')):
    raise RuntimeError('Sniper not compiled at [%s]' % config['sniper_root'])

  if os.path.isfile(os.path.join(config['pin_kit'],'pin.sh')):
    config['pin_bin'] = os.path.join(config['pin_kit'],'pin.sh')
  else:
    config['pin_bin'] = os.path.join(config['pin_kit'],'pin')
  return

def setup_output_dir(config):
  mkdir_p(config['output_base_dir'])
  try:
    os.remove(config['log_file'])
  except OSError:
    pass

def update_config_defaults(config):
  data_dir = glob.glob(config['output_base_dir_default'] + '/*.Data')
  config['data_dir'] = data_dir[0]

def run(app_cmd, update_config, res_tab=[]):
  config = create_default_config()
  config.update(update_config)
  add_dependent_config(config)
  check_dep(config)

  if config['native_run']:
    config['logging'] = False
    run_native(config)
    return
  if config['force']:
    setup_output_dir(config)
    if not config['reuse_profile']:
      if not config['binary_profile']:
        make_mt_pinball(config)
      gen_dcfg(config)
      gen_bbv(config)
      gen_cluster(config)
    else:
      update_config_defaults(config)
    run_sniper(config)
  res_tab.append(evaluate(config))
  return

if __name__ == '__main__':

  def usage(rc = 1):
    import imp
    def import_app(name):
      file, pathname, description = imp.find_module(name)
      return imp.load_module(name, file, pathname, description)
    print 'Benchmarks:'
    for module in import_app('suites').modules:
      module = import_app('apps/' + module)
      print ' ', module.__name__.split('/')[-1] + ':'
      print '   ', ' '.join(module.allbenchmarks())
    print '''
The tool runs end-to-end LoopPoint sampling methodology targeting multi-threaded applications.
Usage:
    run-looppoint.py
    [-h | --help]: Help
    [-n | --ncores=<num of threads> (8)]
    [-i | --input-class=<input class> (test)]
    [-w | --wait-policy=<omp wait policy> (passive)]
    [-p | --program=<suite-application-input> (demo-matrix-1)]: Ex. demo-dotproduct-1,cpu2017-bwaves-1
    [-c | --custom-cfg=<cfg-file>]: Run a workload of interest using cfg-file in the current directory (See README.md)
    [--force]: Start a new set of end-to-end run
    [--reuse-profile]: Reuse the profiling data (used along with --force)
    [--reuse-fullsim]: Reuse the full program simulation (used along with --force)
    [--no-validate]: Skip full program simulation and display only the sampled simulation result (used along with --force)
    [--no-flowcontrol]: Disable thread flowcontrol during profiling
    [--use-pinplay]: Use PinPlay instead of SDE for profiling
    [--binary-profile]: Use the application binary for analysis instead of deterministic analysis with Pinballs
    [--native]: Run the application natively (no sampling/simulation)

    Example:> ./run-looppoint.py -n 8 -i test -p demo-matrix-1 --force --no-validate
    Example:> /path/to/looppoint/run-looppoint.py -n 8 -w active -c matmul.1.cfg --force
    '''
    sys.exit(rc)

  update_config = {}
  suite_apps = []
  custom_cfg = False
  native_run = False
  validate = True
  try:
    opts, args = getopt.getopt(sys.argv[1:], 'hn:i:w:p:c:', [ 'help', 'ncores=', 'input-class=', 'wait-policy=', 'program=', 'custom-cfg=', 'force', 'reuse-profile', 'reuse-fullsim', 'no-validate', 'no-flowcontrol', 'use-pinplay', 'binary-profile', 'native' ])
  except getopt.GetoptError, e:
    # print help information and exit:
    print e
    usage()
  for o, a in opts:
    if o == '-h' or o == '--help':
      usage(0)
    if o == '-n' or o == '--ncores':
      update_config['ncores'] = a
    if o == '-i' or o == '--input-class':
      update_config['input_class'] = a
    if o == '-w' or o == '--wait-policy':
      update_config['wait_policy'] = a
    if o == '-p' or o == '--program':
      suite_apps = a.split(',')
    if o == '-c' or o == '--custom-cfg':
      update_config['custom_cfg'] = os.path.abspath(a)
      custom_cfg = True
    if o == '--force':
      update_config['force'] = True
    if o == '--reuse-profile':
      update_config['reuse_profile'] = True
    if o == '--reuse-fullsim':
      update_config['reuse_fullsim'] = True
    if o == '--no-validate':
      update_config['validate'] = False
      validate = False
    if o == '--no-flowcontrol':
      update_config['flowcontrol'] = False
    if o == '--use-pinplay':
      update_config['use_pinplay'] = True
    if o == '--binary-profile':
      update_config['binary_profile'] = True
    if o == '--native':
      update_config['native_run'] = True
      native_run = True

  if suite_apps and custom_cfg:
    print('Cannot run a default application (--program) while using --custom-cfg')
    usage()
  if 'reuse_fullsim' in update_config and update_config['reuse_fullsim'] and not validate:
    print('Cannot use --reuse-fullsim and --no-validate together')
    usage()
  res_tab = []

  if suite_apps:
    for suite_app in suite_apps:
      suite_app = suite_app.strip()
      if suite_app.count('-') > 0:
        update_config['bm_suite'] = suite_app.split('-')[0]
      if suite_app.count('-') == 1:
        update_config['bm_name'] = suite_app.split('-')[-1]
      if suite_app.count('-') >= 2:
        update_config['bm_name'] = suite_app.split('-', 1)[-1].rsplit('-', 1)[0]
        update_config['bm_input'] = suite_app.split('-')[-1]
      run(args, update_config, res_tab)
  else:
    run(args, update_config, res_tab)

  if not native_run:
    print
    if validate:
      print (tabulate(res_tab, headers = [ 'application', 'runtime\nactual (ns)', 'runtime\npredicted (ns)', 'error\n(%)', 'speedup\n(parallel)', 'speedup\n(serial)', 'coverage\n(%)' ], tablefmt = 'pretty', floatfmt='.2f', colalign=('left', 'center', 'center', 'center', 'center', 'center', 'center')))
    else:
      print (tabulate(res_tab, headers = [ 'application', 'runtime\npredicted (ns)', 'coverage\n(%)' ], tablefmt = 'pretty', floatfmt='.2f', colalign=('left', 'center', 'center')))
    print
