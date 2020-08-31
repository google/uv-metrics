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

from google.cloud import pubsub_v1
import json
import mlflow as mlf
from mlflow.entities import Param, Metric, RunTag
import time
from typing import Optional, Dict, List, Any
import uv.reporter.base as b
import uv.types as t


def _metric_to_dict(m: Metric) -> Dict[str, Any]:
  return {
      'key': m.key,
      'value': m.value,
      'timestamp': m.timestamp,
      'step': m.step,
  }


class MLFlowReporter(b.AbstractReporter):
  """Reporter implementation that logs metrics to mlflow.
  Args:
  pubsub_topic: if specified, metrics are published to this google
                cloud pubsub topic instead of directly to mlflow
  """

  def __init__(self, pubsub_topic: str = None):
    self._client = mlf.tracking.MlflowClient()
    self._topic = pubsub_topic
    self._publisher: Optional[pubsub_v1.PublisherClient] = None

    if pubsub_topic is not None:
      self._publisher = pubsub_v1.PublisherClient()

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

    # we are using pubsub for metrics
    if self._publisher is not None and len(metrics):
      self._publisher.publish(
          self._topic,
          json.dumps({
              'run_id': run_id,
              'metrics': [_metric_to_dict(m) for m in metrics]
          }).encode('utf-8'),
      )
      metrics = []

    if len(params) or len(tags) or len(metrics):
      self._client.log_batch(run_id=run_id,
                             metrics=metrics,
                             params=params,
                             tags=tags)

  def report_param(self, k: str, v: str) -> None:
    self.report_params({k: v})

  def report_params(self, m: Dict[str, str]) -> None:
    self._log_batch(params=[Param(k, str(v)) for k, v in m.items()])

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    ts = int(time.time() * 1000)
    self._log_batch(metrics=[Metric(k, v, ts, step) for k, v in m.items()])

  def report(self, step: int, k: t.MetricKey, v: t.Metric) -> None:
    self.report_all(step=step, m={k: v})
