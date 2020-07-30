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

from typing import Dict

import mlflow
import uv.reporter.base as b
import uv.types as t


class MLFlowReporter(b.AbstractReporter):
  """Reporter implementation that logs metrics to mlflow."""

  def __init__(self):
    pass

  def report_param(self, k: str, v: str) -> None:
    mlflow.log_param(k, v)

  def report_params(self, m: Dict[str, str]) -> None:
    mlflow.log_params(m)

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    mlflow.log_metrics(m, step=step)

  def report(self, step: int, k: t.MetricKey, v: t.Metric) -> None:
    mlflow.log_metric(key=k, value=v, step=step)
