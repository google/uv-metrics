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

import google.cloud.pubsub_v1
import json
import mlflow as mlf
from mlflow.entities import Metric
import pytest
import tempfile

import uv
from uv.mlflow.reporter import MLFlowPubsubReporter
from uv.resources.mlflow_subscriber import log_metrics

_MSG_QUEUE = []


def _reset_experiment():
  # this is needed because the active experiment in mlflow is sticky, so if
  # an earlier test sets this, then things fail here when we don't use
  # an explicit experiment
  mlf.set_experiment(mlf.entities.Experiment.DEFAULT_EXPERIMENT_NAME)


class MockMessage(object):
  '''mock google.cloud.pubsub_v1.subscriber.message.Message'''

  def __init__(self, data: bytes):
    self.data = data

  def ack(self):
    pass


@pytest.fixture
def mock_pubsub(monkeypatch):
  '''mock out pubsub_v1 PublisherClient'''

  class MockClient():

    def __init__(self, batch_settings=(), publisher_options=(), **kwargs):
      _MSG_QUEUE = []

    def publish(self, topic: str, msg: bytes):
      _MSG_QUEUE.append(MockMessage(msg))

    @staticmethod
    def topic_path(project: str, topic: str) -> str:
      return f'projects/{project}/topics/{topic}'

  monkeypatch.setattr(google.cloud.pubsub_v1, 'PublisherClient', MockClient)


def test_log_metrics(mock_pubsub):
  '''tests the log_metrics() funtion in mlflow_subscriber'''

  # test exception handling by passing invalid message and mlflow client
  log_metrics(None, None, True)

  with tempfile.TemporaryDirectory() as tmpdir:
    mlf.set_tracking_uri(f'file:{tmpdir}/foo')
    _reset_experiment()

    mlflow_cfg = {
        'experiment_name': 'foo',
        'run_name': 'bar',
        'artifact_location': '/foo/bar',
    }

    with uv.start_run(**mlflow_cfg), uv.active_reporter(
        MLFlowPubsubReporter('p', 't')) as r:
      active_run = mlf.active_run()
      steps = [{
          'step': 1,
          'm': {
              'a': 3,
              'b': 3.141
          }
      }, {
          'step': 2,
          'm': {
              'a': 6,
              'b': 6.282
          }
      }]

      client = mlf.tracking.MlflowClient()

      assert len(_MSG_QUEUE) == 0

      for s in steps:
        r.report_all(**s)

      assert len(_MSG_QUEUE) == len(steps)
      for m in _MSG_QUEUE:
        log_metrics(client, m, True)

      run = client.get_run(active_run.info.run_id)
      assert run is not None

      metrics = run.data.metrics

      metric_data = {}
      # check that the metrics are in the run data
      for k, v in steps[0]['m'].items():
        assert k in metrics
        metric_data[k] = {
            x.step: x.value
            for x in client.get_metric_history(active_run.info.run_id, k)
        }

      for s in steps:
        cur_step = s['step']
        for k, v in s['m'].items():
          assert metric_data[k][cur_step] == v
