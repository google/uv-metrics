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

import google.cloud.pubsub_v1
import json
import logging
import mlflow as mlf
from mlflow.entities import Param, Metric, RunTag
import numbers
import numpy as np
import os
import re
import time
from typing import Optional, Dict, List, Union, Any
import uv.reporter.base as b
import uv.types as t
import uv.util as u
import uv.util.attachment as ua

PUBSUB_PROJECT_ENV_VAR = "UV_MLFLOW_PUBSUB_PROJECT"
PUBSUB_TOPIC_ENV_VAR = "UV_MLFLOW_PUBSUB_TOPIC"

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


def _sanitize_metric_value(k: t.MetricKey, v: t.Metric) -> t.Metric:
  '''sanitizes a metric value, if non-numeric, raises ValueError'''

  # we support length-one numpy arrays of valid types
  if isinstance(v, np.ndarray):
    if len(v) != 1:
      raise ValueError('only length-one numpy arrays are supported')
    else:
      v = v[0]

  if not isinstance(v, numbers.Number):
    raise ValueError('metric must be an instance of numbers.Number')

  try:
    v = float(v)
  except:
    raise ValueError('metric must be convertible to float')

  return v


def _sanitize_metrics(
    d: Dict[t.MetricKey, t.Metric]) -> Dict[t.MetricKey, t.Metric]:
  '''sanitizes keys to conform to mlflow restrictions, and
  raises ValueError if value type is not supported'''

  return {sanitize_key(k): _sanitize_metric_value(k, v) for k, v in d.items()}


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
    flat_m = ua.flatten(m)
    self._log_batch(params=[
        Param(sanitize_key(k), _sanitize_param_value(str(v)))
        for k, v in flat_m.items()
    ])

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    m = _sanitize_metrics(m)
    ts = int(time.time() * 1000)
    self._log_batch(metrics=[Metric(k, v, ts, step) for k, v in m.items()])

  def report(self, step: int, k: t.MetricKey, v: t.Metric) -> None:
    self.report_all(step=step, m={k: v})


def _metric_dict(
    key: str,
    value: float,
    timestamp: float,
    step: int,
) -> Dict[str, Any]:
  '''create a dictionary describing an mlflow metric'''
  return {
      'key': key,
      'value': value,
      'timestamp': timestamp,
      'step': step,
  }


class MLFlowPubsubReporter(b.AbstractReporter):
  """Reporter implementation that logs metrics to mlflow using
  gcp pubsub.

  Args:

  project: gcp project for pubsub, defaults to UV_MLFLOW_PUBSUB_PROJECT
           env var
  topic: pubsub topic, defaults to UV_MLFLOW_PUBSUB_TOPIC env var
  """

  def __init__(
      self,
      project: Optional[str] = None,
      topic: Optional[str] = None,
  ):
    project = project or os.getenv(PUBSUB_PROJECT_ENV_VAR)
    if project is None:
      raise ValueError(f'project must be specified or the '
                       f'{PUBSUB_PROJECT_ENV_VAR} env var must be set')

    topic = topic or os.getenv(PUBSUB_TOPIC_ENV_VAR)
    if topic is None:
      raise ValueError(f'topic must be specified or the '
                       f'{PUBSUB_TOPIC_ENV_VAR} env var must be set')

    self._base_reporter = MLFlowReporter()
    self._publisher = google.cloud.pubsub_v1.PublisherClient()
    self._topic = self._publisher.topic_path(project, topic)

  def report_param(self, k: str, v: str) -> None:
    self._base_reporter.report_param(k, v)

  def report_params(self, m: Dict[str, str]) -> None:
    self._base_reporter.report_params(m)

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    ts = int(time.time() * 1000)
    m = _sanitize_metrics(m)
    self._publisher.publish(
        self._topic,
        json.dumps({
            'run_id': mlf.active_run().info.run_id,
            'metrics': [_metric_dict(k, v, ts, step) for k, v in m.items()]
        }).encode('utf-8'),
    )

  def report(self, step: int, k: t.MetricKey, v: t.Metric) -> None:
    self.report_all(step=step, m={k: v})
