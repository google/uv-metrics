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
"""Reporter interface and implementations."""

import os
from contextlib import contextmanager
from typing import Dict

import mlflow as mlf
import uv.types as t
import uv.util.env as ue
from uv.reporter.base import AbstractReporter
from uv.reporter.store import NullReporter

_active_reporter = None


def get_reporter() -> AbstractReporter:
  """Returns the active reporter set using set_reporter()"""
  if _active_reporter is not None:
    return _active_reporter
  return NullReporter()


def set_reporter(r: AbstractReporter) -> AbstractReporter:
  """Set the globally available reporter instance. Returns its input."""
  global _active_reporter
  _active_reporter = r


@contextmanager
def active_reporter(r: AbstractReporter):
  old_reporter = _active_reporter
  globals()['_active_reporter'] = r
  yield
  globals()['_active_reporter'] = old_reporter


def report(step: int, k: t.MetricKey, v: t.Metric) -> None:
  """Accepts a step (an ordered int referencing some timestep), a metric key and
    a value, and persists the metric into the globally available reporter
    returned by uv.get_reporter().

  """
  return get_reporter().report(step, k, v)


def report_all(step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
  """Accepts a step (an ordered int referencing some timestep) and a dictionary
    of metric key => metric value, and persists the metric into the globally
    available reporter returned by uv.get_reporter().

  """
  return get_reporter().report_all(step, m)


def report_param(k: str, v: str) -> None:
  """Accepts a key and value parameter and logs these as parameters alongside the
    reported metrics. Reports to the globally available reporter returned by
    uv.get_reporter().

    """
  return get_reporter().report_param(k, v)


def report_params(m: Dict[str, str]) -> None:
  """Accepts a dict of parameter name -> value, and logs these as parameters
  alongside the reported metrics. Reports to the globally available reporter
  returned by uv.get_reporter().

  """
  return get_reporter().report_params(m)


def start_run(param_prefix: str = None, experiment_name: str = None, **args):
  """Close alias of mlflow.start_run. The only difference is that uv.start_run
  attempts to extract parameters from the environment and log those to the
  bound UV reporter using `report_params`.

  """
  if experiment_name is None:
    experiment_name = os.environ.get("MLFLOW_EXPERIMENT_NAME")

  # Make sure the experiment exists before the run starts.
  if experiment_name is not None:
    mlf.set_experiment(experiment_name)

  ret = mlf.start_run(**args)
  env_params = ue.extract_params(prefix=param_prefix)
  mlf.set_tags(env_params)
  return ret
