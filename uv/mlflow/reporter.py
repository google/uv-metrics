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
import time
from typing import Optional, Dict, List
import uv.reporter.base as b
import uv.types as t


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

  def report_params(self, m: Dict[str, str]) -> None:
    self._log_batch(params=[Param(k, str(v)) for k, v in m.items()])

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    ts = int(time.time() * 1000)
    self._log_batch(metrics=[Metric(k, v, ts, step) for k, v in m.items()])

  def report(self, step: int, k: t.MetricKey, v: t.Metric) -> None:
    self.report_all(step=step, m={k: v})
