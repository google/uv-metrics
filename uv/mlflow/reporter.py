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
"""MLFlow reporter that conforms to UV's reporter interface."""

import mlflow as mlf
from mlflow.entities import Param, Metric, RunTag
import re
import time
from typing import Optional, Dict, List, Union
import uv.reporter.base as b
import uv.types as t
from uv.mlflow import utils

INVALID_CHAR_REPLACEMENT = '-'

# mlflow restricts these strings
_INVALID_PARAM_AND_METRIC_NAMES = re.compile('[^/\w.\- ]')


def _truncate_key(k: str) -> str:
  '''truncates keys for mlflow, as there are strict limits for key length'''
  return k[:mlf.utils.validation.MAX_ENTITY_KEY_LENGTH]


def sanitize_key(k: str) -> str:
  '''sanitizes keys for mlflow to conform to mlflow restrictions'''
  return _INVALID_PARAM_AND_METRIC_NAMES.sub(INVALID_CHAR_REPLACEMENT,
                                             _truncate_key(k))


def _sanitize_param_value(v: str):
  '''sanitizes parameter values to conform to mlflow restrictions'''
  return v[:mlf.utils.validation.MAX_PARAM_VAL_LENGTH]


class MLFlowReporter(b.AbstractReporter):
  """Reporter implementation that logs metrics to mlflow."""

  def __init__(self):
    self._client = mlf.tracking.MlflowClient()

  def _log_batch(
      self,
      run_id: Optional[str] = None,
      metrics: Optional[List[Metric]] = None,
      params: Optional[List[Param]] = None,
      tags: Optional[List[RunTag]] = None,
  ) -> None:
    run_id = run_id or mlf.active_run().info.run_id
    metrics = metrics or []
    params = params or []
    tags = tags or []

    self._client.log_batch(run_id=run_id,
                           metrics=metrics,
                           params=params,
                           tags=tags)

  def report_param(self, k: str, v: str) -> None:
    self.report_params({k: v})

  def report_params(self, m: Dict[str, Union[str, Dict]]) -> None:
    flat_m = utils.flatten(m)
    self._log_batch(params=[
        Param(sanitize_key(k), _sanitize_param_value(str(v)))
        for k, v in flat_m.items()
    ])

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    ts = int(time.time() * 1000)
    self._log_batch(
        metrics=[Metric(sanitize_key(k), v, ts, step) for k, v in m.items()])

  def report(self, step: int, k: t.MetricKey, v: t.Metric) -> None:
    self.report_all(step=step, m={k: v})
