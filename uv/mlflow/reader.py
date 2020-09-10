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
"""Tests of the various reporter store implementations."""

from collections import OrderedDict

import hypothesis.strategies as st
import mlflow
import numpy as np
import tests.uv.util.test_init as ti
import uv.reporter.store as rs
from hypothesis import given
from uv.mlflow import MLFlowReporter

import pytest

client = mlflow.tracking.MlflowClient()


def get_experiments(exp_names):
  """Returns a sequence of experiments, given the names.

  The names of the experiments can come from your logs, or from the caliban
  status UI.

  """
  return [client.get_experiment_by_name(name) for name in exp_names]


def metric_array(client, run_id, metric):
  """Returns a numpy array containing the list of timeseries data for the
  requested metric.

  """
  return np.array([
      x.value for x in sorted(client.get_metric_history(run_id, metric),
                              key=lambda x: x.step)
  ])


def reader_result(runs, metrics):
  """`metrics` here is a sequence of the metrics you reported. `runs` is a list
  of the runs you requested.

  The return value is a dictionary of run_name -> metric dictionary, that fits
  the same interface as the UV Readers currently return. So we have one
  wrapping layer (2 make sense, given the multi-experiment search ability.)

  So, the trick here will be helping you make the link between the query you
  made, and the actual run ID here.

  """
  metrics = {}
  for r in runs:
    run_id = r.info.run_id
    run_name = r.data.tags['mlflow.runName']
    metrics[run_name] = {k: metric_array(client, run_id, k) for k in metrics}

  return metrics


def interface_sketch():
  """Objectives:

  Provide an interface that is very similar to the UV Reader interface. That
  takes you from a list of metrics that you pass into a particular reader => a
  dict of metric_name => timeseries.

  We have two additional levels of nesting:
  - experiment
  - run

  And we want users to be able to write a query string in some form, and get
  back a data structure like this:

  Dict[Experiment, Dict[RunID, {
    "metrics": Dict[MetricName, List[Metric+Step]],
    "params":  Dict[K, V]
  }]

  What query language?

  - the one MLFlow exposes has to work.

  - We can also attempt to "match" parameters, ie flags, that the user has
    logged. The trick here will be letting the user perform

  - one query to get all of the data, and then
  - another query to filter the actual data structure that they have with them,
    to pluck out a particular run and just look at it.

  """
  # You have to start by knowing the name of an experiment.
  #
  # Q - how do you know what experiment or run you're interested in? you can
  # get this from the UI.

  # This is the current interface.
  client = mlflow.tracking.MlflowClient()
  experiments = get_experiments(["my_experiment"])

  # You can also list all experiments and filter by the user's name, list artifacts, etc.
  ids = [x.experiment_id for x in experiments]

  # Now we can go search for runs.
  qualifying_runs = client.search_runs(
      experiment_ids=ids,
      # This is the same filter string that we can get from the UI's data
      # structure. I propose we adopt their language, of course.
      #
      # I propose we take a dict of flag settings here and generate a filter
      # string, or let someone query it directly.
      filter_string='params.mean = "0"',
  )
  metrics = ["test.loss", "train.loss", "model.l2"]
  result_dict = reader_result(qualifying_runs, metrics)

  # These are the raw materials. On top of this, we'd like a library of
  # functions that can process the format of the underlying metrics into
  # charts.
  #
  # - generate plots for individual metrics vs time
  #
