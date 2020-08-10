#!/usr/bin/python
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''a very simple MLFlowReporter example for UV'''

import argparse
import sys
import uv
from uv.mlflow.reporter import MLFlowReporter

_DESCRIPTION = '''
A simple UV mlflow reporter example.

This example will run a simple program and log results to your current directory
under './mlruns' by default. To view the results, run a local mlflow ui server in the
same directory:

mlflow ui

By default, this will serve results at http://localhost:5000.

You can change the mlflow experiment and run names by setting the environment
variables MLFLOW_EXPERIMENT_NAME and MLFLOW_RUN_NAME, respectively, or you can set
them in the uv.start_run() method. You can also use an existing MLFlow tracking
server by setting the MLFLOW_TRACKING_URI environment variable.

More information on MLFlow tracking can be found at
https://mlflow.org/docs/latest/tracking.html
'''


def _parser():
  parser = argparse.ArgumentParser(
      description=_DESCRIPTION,
      prog='tutorial',
      formatter_class=argparse.RawTextHelpFormatter)

  parser.add_argument("--steps", type=int, help='number of steps', default=8)
  parser.add_argument("--slope", type=float, help='slope', default=1)
  return parser


def _parse_flags(argv):
  return _parser().parse_args(argv[1:])


def _run_training(steps: int, slope: float):
  for i in range(steps):
    uv.report(step=i, k='metric_0', v=i * slope)


def main(**kwargs):

  with uv.start_run(), uv.active_reporter(MLFlowReporter()):
    uv.report_params(kwargs)
    _run_training(**kwargs)


if __name__ == '__main__':
  main(**vars(_parse_flags(sys.argv)))
