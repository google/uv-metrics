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
'''A MLFlow+UV tutorial showing how to query results from multiple runs.'''

import getpass
import mlflow
import numpy as np
import os
import uv
from uv.mlflow.reporter import MLFlowReporter

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

_DESCRIPTION = '''
A MLFlow+UV tutorial showing how to query results from multiple runs.

Please note that this tutorial requires the matplotlib and numpy packages.

This example will run a simple program and log results to your current directory
under './mlruns' by default. To view the results, run a local mlflow ui server in the
same directory:

mlflow ui

By default, this will serve results at http://localhost:5000.

More information on MLFlow tracking can be found at
https://mlflow.org/docs/latest/tracking.html

This tutorial will also create a plot called 'mlflow_query_tutorial.png' of some of its metric
data in the repo docs directory if it is accessible, or in your local directory.
'''

# simple set of parameters for our runs
PARAMETERS = [{
    'mean': 0,
    'std': 0.1
}, {
    'mean': 0,
    'std': 0.2
}, {
    'mean': 1,
    'std': 0.1
}]


def _gaussian(x: float, mean: float, std: float) -> float:
  return np.exp(-0.5 * ((x - mean) / std)**2) / (std * np.sqrt(2 * np.pi))


def _compute(mean: float, std: float):
  '''performs a single compute run, logging metrics to mlflow'''
  fn = lambda x: _gaussian(x, mean, std)

  for i in range(2):  #64):
    x = (i / 32.0) - 1
    metrics = {'x': x, 'y': fn(x)}
    uv.report_all(step=i, m=metrics)


def _run_experiments(experiment_name: str):
  '''performs runs for each of our parameter settings, creating the
  associated mlflow objects and logging paramters'''

  for i, p in enumerate(PARAMETERS):
    with uv.start_run(
        experiment_name=experiment_name,
        run_name=f'run_{i}',
    ):
      uv.report_params(p)
      _compute(**p)


def _get_metric_array(client: mlflow.tracking.MlflowClient, run_id: str,
                      metric: str) -> np.ndarray:
  '''gets metric data from mlflow and converts it to a numpy array'''
  return np.array([
      x.value for x in sorted(client.get_metric_history(run_id, metric),
                              key=lambda x: x.step)
  ])


def main():

  experiment_name = f'{getpass.getuser()}_query_tutorial'

  with uv.active_reporter(MLFlowReporter()):
    _run_experiments(experiment_name)

  client = mlflow.tracking.MlflowClient()
  experiment = client.get_experiment_by_name(experiment_name)

  # get all of our runs where we set mean=0
  mean_zero_runs = client.search_runs(
      experiment_ids=[experiment.experiment_id],
      filter_string='params.mean = "0"',
  )

  # extract metric data
  metrics = {}
  for r in mean_zero_runs:
    run_id = r.info.run_id
    run_name = r.data.tags['mlflow.runName']
    metrics[run_name] = {
        k: _get_metric_array(client, run_id, k) for k in ('x', 'y')
    }

  # generate a simple plot and save it to file
  for k, v in metrics.items():
    plt.plot(v['x'], v['y'], label=k)
  plt.legend()
  plt.grid(True)
  plt.title('UV/MLFlow Tutorial')

  outdir = '../../docs/_static/img/'
  if not os.path.exists(outdir):
    outdir = '.'

  outfile = os.path.join(outdir, 'mlflow_query_tutorial.png')
  plt.savefig(outfile)
  print(f'plot saved to {outfile}')

  # we can also log this plot as an artifact
  artifact_run = mean_zero_runs[0]
  run_id = artifact_run.info.run_id
  client.log_artifact(run_id=run_id, local_path=outfile)
  print(f'artifact saved to run {artifact_run.data.tags["mlflow.runName"]}')

  # you can list a job's artifacts using list_artifacts()
  print(f'artifacts for run_id {run_id}:')
  artifacts = client.list_artifacts(run_id=run_id)
  for a in artifacts:
    print(f'{a}')

  # to retrieve an artifact, use client.download_artifacts()
  download_path = '.'
  client.download_artifacts(run_id=run_id, path=artifacts[0].path, dst_path='.')


if __name__ == '__main__':
  main()
