# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Integration code for AFL fuzzer."""

import json
import os
import shutil
import subprocess

from fuzzers import utils


def prepare_build_environment():
    """Set environment variables used to build targets for AFL-based
    fuzzers."""
    cflags = ['-fPIC']
    utils.append_flags('CFLAGS', cflags)
    utils.append_flags('CXXFLAGS', cflags)

    os.environ['CC'] = 'clang'
    os.environ['CXX'] = 'clang++'
    os.environ['FUZZER_LIB'] = '/libAFL.a'


def build():
    """Build benchmark."""
    prepare_build_environment()

    utils.build_benchmark()

    print('[post_build] Copying afl-fuzz to $OUT directory')
    # Copy out the afl-fuzz binary as a build artifact.
    shutil.copy('/afl/afl-fuzz', os.environ['OUT'])
    shutil.copytree('/rw', os.environ['OUT'] + '/rw')
    shutil.copy('/rw/rwtools_x64/gen_block_score.py', os.environ['OUT'])


def get_stats(output_corpus, fuzzer_log):  # pylint: disable=unused-argument
    """Gets fuzzer stats for AFL."""
    # Get a dictionary containing the stats AFL reports.
    stats_file = os.path.join(output_corpus, 'fuzzer_stats')
    with open(stats_file) as file_handle:
        stats_file_lines = file_handle.read().splitlines()
    stats_file_dict = {}
    for stats_line in stats_file_lines:
        key, value = stats_line.split(': ')
        stats_file_dict[key.strip()] = value.strip()

    # Report to FuzzBench the stats it accepts.
    stats = {'execs_per_sec': float(stats_file_dict['execs_per_sec'])}
    return json.dumps(stats)


def prepare_fuzz_environment(input_corpus):
    """Prepare to fuzz with AFL or another AFL-based fuzzer."""
    # Tell AFL to not use its terminal UI so we get usable logs.
    os.environ['AFL_NO_UI'] = '1'
    # Skip AFL's CPU frequency check (fails on Docker).
    os.environ['AFL_SKIP_CPUFREQ'] = '1'
    # No need to bind affinity to one core, Docker enforces 1 core usage.
    os.environ['AFL_NO_AFFINITY'] = '1'
    # AFL will abort on startup if the core pattern sends notifications to
    # external programs. We don't care about this.
    os.environ['AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES'] = '1'
    # Don't exit when crashes are found. This can happen when corpus from
    # OSS-Fuzz is used.
    os.environ['AFL_SKIP_CRASHES'] = '1'
    # Shuffle the queue
    os.environ['AFL_SHUFFLE_QUEUE'] = '1'

    # AFL needs at least one non-empty seed to start.
    utils.create_seed_file_for_empty_corpus(input_corpus)
    
    # Install requirements for rw
    subprocess.check_call(['pip3', 'install', '-r', '/out/rw/requirements.txt', '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    # Install llvm
    try:
        res = subprocess.check_call(['apt-get', 'install', '-y', 'llvm'])
        print(res)
    except subprocess.CalledProcessError as exc:
        print('returncode:', exc.returncode)
    # subprocess.check_call(['apt-get', 'install', 'llvm'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def check_skip_det_compatible(additional_flags):
    """ Checks if additional flags are compatible with '-d' option"""
    # AFL refuses to take in '-d' with '-M' or '-S' options for parallel mode.
    # (cf. https://github.com/google/AFL/blob/8da80951/afl-fuzz.c#L7477)
    if '-M' in additional_flags or '-S' in additional_flags:
        return False
    return True


def afl_instrumentation_by_rw(target_binary):
    """ [self] AFL instrumentation and analysis on binary """
    print('[analyse_by_rw] AFL instrumentation and analysis on binary by retrowrite')
    target_binary_afl_dis = target_binary + '_afl.s'
    target_binary_afl = target_binary + '_afl'
    command = [
        'python',
        '/out/rw/retrowrite',
        '-f',
        target_binary,
        target_binary_afl_dis,
        '--ignore-no-pie'
    ]

    try:
        res = subprocess.check_call(command)
        print(res)
    except subprocess.CalledProcessError as exc:
        print('returncode:', exc.returncode)
        print('cmd:', exc.cmd)
        print('output:', exc.output)

    try:
        res = subprocess.check_call(['llvm-mc', target_binary_afl_dis, '-o', target_binary_afl])
        print(res)
    except subprocess.CalledProcessError as exc:
        print('returncode:', exc.returncode)


def run_afl_fuzz(input_corpus,
                 output_corpus,
                 target_binary,
                 additional_flags=None,
                 hide_output=False):
    """Run afl-fuzz."""
    # Spawn the afl fuzzing process.
    print('[run_afl_fuzz] Running target with afl-fuzz')
    command = [
        './afl-fuzz',
        '-i',
        input_corpus,
        '-o',
        output_corpus,
        # Use no memory limit as ASAN doesn't play nicely with one.
        '-m',
        'none',
        '-t',
        '1000+',  # Use same default 1 sec timeout, but add '+' to skip hangs.
    ]
    # Use '-d' to skip deterministic mode, as long as it it compatible with
    # additional flags.
    if not additional_flags or check_skip_det_compatible(additional_flags):
        command.append('-d')
    if additional_flags:
        command.extend(additional_flags)
    dictionary_path = utils.get_dictionary_path(target_binary)
    if dictionary_path:
        command.extend(['-x', dictionary_path])
    command += [
        '--',
        target_binary + '_afl',
        # Pass INT_MAX to afl the maximize the number of persistent loops it
        # performs.
        '2147483647'
    ]
    output_stream = subprocess.DEVNULL if hide_output else None
    
    print('[run_afl_fuzz] Running command: python gen_block_score.py')
    proc1 = subprocess.Popen(['python', 'gen_block_score.py'], stdout=output_stream, stderr=output_stream)
    proc2 = subprocess.Popen(['sleep', '20'], stdout=output_stream, stderr=output_stream)
    
    if proc2.wait() == 0:
        print('[run_afl_fuzz] Running command: ' + ' '.join(command))
        proc3 = subprocess.Popen(command, stdout=output_stream, stderr=output_stream)


def fuzz(input_corpus, output_corpus, target_binary):
    """Run afl-fuzz on target."""
    prepare_fuzz_environment(input_corpus)

    afl_instrumentation_by_rw(target_binary)
    run_afl_fuzz(input_corpus, output_corpus, target_binary)
