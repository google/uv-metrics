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

import numbers
import numpy as np
import google.cloud.pubsub_v1
import json
import mlflow as mlf
from mlflow.entities import Metric
import pytest
import tempfile
import tensorflow as tf

import uv
from uv.mlflow.reporter import (MLFlowReporter, MLFlowPubsubReporter,
                                PUBSUB_PROJECT_ENV_VAR, PUBSUB_TOPIC_ENV_VAR)
import uv.util as u


@pytest.fixture
def mock_pubsub(monkeypatch):

  class MockClient():

    def __init__(self, batch_settings=(), publisher_options=(), **kwargs):
      pass

    def publish(self, topic: str, msg: bytes):
      d = json.loads(msg.decode('utf-8'))
      run_id = d['run_id']
      metrics = [Metric(**x) for x in d['metrics']]
      mlf.tracking.MlflowClient().log_batch(run_id=run_id, metrics=metrics)

    @staticmethod
    def topic_path(project: str, topic: str) -> str:
      return f'projects/{project}/topics/{topic}'

  monkeypatch.setattr(google.cloud.pubsub_v1, 'PublisherClient', MockClient)


# this is a simple invalid key for mlflow to test our sanitizer
INVALID_KEY = '+' + 'x' * (mlf.utils.validation.MAX_ENTITY_KEY_LENGTH)
SANITIZED_KEY = uv.mlflow.reporter.INVALID_CHAR_REPLACEMENT + 'x' * (
    mlf.utils.validation.MAX_ENTITY_KEY_LENGTH - 1)

INVALID_PARAM_VALUE = 'z' * (mlf.utils.validation.MAX_PARAM_VAL_LENGTH + 1)
SANITIZED_PARAM_VALUE = INVALID_PARAM_VALUE[:mlf.utils.validation.
                                            MAX_PARAM_VAL_LENGTH]


def _reset_experiment():
  # this is needed because the active experiment in mlflow is sticky, so if
  # an earlier test sets this, then things fail here when we don't use
  # an explicit experiment
  mlf.set_experiment(mlf.entities.Experiment.DEFAULT_EXPERIMENT_NAME)


@pytest.mark.parametrize(
    'reporter', [MLFlowReporter, lambda: MLFlowPubsubReporter('p', 't')])
def test_report_params(mock_pubsub, reporter):
  with tempfile.TemporaryDirectory() as tmpdir:
    mlf.set_tracking_uri(f'file:{tmpdir}/foo')
    _reset_experiment()

    mlflow_cfg = {
        'experiment_name': 'foo',
        'run_name': 'bar',
        'artifact_location': '/foo/bar',
    }

    with uv.start_run(**mlflow_cfg) as active_run, uv.active_reporter(
        reporter()) as r:
      assert r is not None

      params = {
          'a': 3,
          'b': 'string_param',
          INVALID_KEY: INVALID_PARAM_VALUE,
      }
      r.report_params(params)

      assert mlf.active_run() == active_run

      # we need to access the run via a client to inspect most params/tags/metrics
      client = mlf.tracking.MlflowClient()
      run = client.get_run(active_run.info.run_id)
      assert run is not None

      for k, v in params.items():
        if k == INVALID_KEY:
          k = SANITIZED_KEY
        if v == INVALID_PARAM_VALUE:
          v = SANITIZED_PARAM_VALUE
        p = run.data.params
        assert k in p
        assert p[k] == str(v)


@pytest.mark.parametrize(
    'reporter', [MLFlowReporter, lambda: MLFlowPubsubReporter('p', 't')])
def test_report_param(mock_pubsub, reporter):
  with tempfile.TemporaryDirectory() as tmpdir:
    mlf.set_tracking_uri(f'file:{tmpdir}/foo')
    _reset_experiment()

    mlflow_cfg = {
        'experiment_name': 'foo',
        'run_name': 'bar',
        'artifact_location': '/foo/bar',
    }

    with uv.start_run(**mlflow_cfg) as active_run, uv.active_reporter(
        reporter()) as r:
      assert r is not None

      param = {'a': 3.14159}
      r.report_param(k='a', v=param['a'])

      assert mlf.active_run() == active_run

      # we need to access the run via a client to inspect most params/tags/metrics
      client = mlf.tracking.MlflowClient()
      run = client.get_run(active_run.info.run_id)
      assert run is not None

      for k, v in param.items():
        p = run.data.params
        assert k in p
        assert p[k] == str(v)


@pytest.mark.parametrize(
    'reporter', [MLFlowReporter, lambda: MLFlowPubsubReporter('p', 't')])
def test_report_all(mock_pubsub, reporter):
  with tempfile.TemporaryDirectory() as tmpdir:
    mlf.set_tracking_uri(f'file:{tmpdir}/foo')
    _reset_experiment()

    mlflow_cfg = {
        'experiment_name': 'foo',
        'run_name': 'bar',
        'artifact_location': '/foo/bar',
    }

    with uv.start_run(**mlflow_cfg) as active_run, uv.active_reporter(
        reporter()) as r:
      assert r is not None

      steps = [{
          'step': 1,
          'm': {
              'a': 3,
              'b': 3.141,
              INVALID_KEY: 1.23,
              'c': np.array([0]),
          }
      }, {
          'step': 2,
          'm': {
              'a': 6,
              'b': 6.282,
              INVALID_KEY: 2.46,
              'c': np.array([4.0]),
          }
      }]

      for p in steps:
        r.report_all(**p)

      assert mlf.active_run() == active_run

      # we need to access the run via a client to inspect most params/tags/metrics
      client = mlf.tracking.MlflowClient()
      run = client.get_run(active_run.info.run_id)
      assert run is not None

      metrics = run.data.metrics

      metric_data = {}
      # check that the metrics are in the run data
      for k, v in steps[0]['m'].items():
        if k == INVALID_KEY:
          k = SANITIZED_KEY
        assert k in metrics
        metric_data[k] = {
            x.step: x.value
            for x in client.get_metric_history(active_run.info.run_id, k)
        }

      for s in steps:
        cur_step = s['step']
        for k, v in s['m'].items():
          if k == INVALID_KEY:
            k = SANITIZED_KEY
          if isinstance(v, np.ndarray):
            v = v[0]
          assert metric_data[k][cur_step] == v


@pytest.mark.parametrize(
    'reporter', [MLFlowReporter, lambda: MLFlowPubsubReporter('p', 't')])
def test_report(mock_pubsub, reporter):
  with tempfile.TemporaryDirectory() as tmpdir:
    mlf.set_tracking_uri(f'file:{tmpdir}/foo')
    _reset_experiment()

    mlflow_cfg = {
        'experiment_name': 'foo',
        'run_name': 'bar',
        'artifact_location': '/foo/bar',
    }

    with uv.start_run(**mlflow_cfg) as active_run, uv.active_reporter(
        reporter()) as r:
      assert r is not None

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

      for p in steps:
        for k, v in p['m'].items():
          r.report(step=p['step'], k=k, v=v)

      assert mlf.active_run() == active_run

      # we need to access the run via a client to inspect most params/tags/metrics
      client = mlf.tracking.MlflowClient()
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


def test_pubsub_env(mock_pubsub, monkeypatch):
  # make sure we assert if no valid project passed
  monkeypatch.delenv(PUBSUB_PROJECT_ENV_VAR, raising=False)
  with pytest.raises(ValueError):
    r = MLFlowPubsubReporter(topic='mlflow')

  # test passing project via env var to pubsub reporter
  monkeypatch.setenv(PUBSUB_PROJECT_ENV_VAR, 'foo')
  r = MLFlowPubsubReporter(topic='mlflow')

  # make sure we assert if no valid topic passed
  monkeypatch.delenv(PUBSUB_TOPIC_ENV_VAR, raising=False)
  with pytest.raises(ValueError):
    r = MLFlowPubsubReporter(project='foo')

  # test passing project and topic via env vars to pubsub reporter
  monkeypatch.setenv(PUBSUB_TOPIC_ENV_VAR, 'mlflow')
  r = MLFlowPubsubReporter(project='foo')

  # test passing both project and topic via env vars
  r = MLFlowPubsubReporter()


@pytest.mark.parametrize(
    'reporter', [MLFlowReporter, lambda: MLFlowPubsubReporter('p', 't')])
@pytest.mark.parametrize(
    'value',
    [np.array([0, 1]), 'foo',
     complex(0), tf.constant([0.2])])
def test_report_invalid(mock_pubsub, reporter, value):
  with tempfile.TemporaryDirectory() as tmpdir:
    mlf.set_tracking_uri(f'file:{tmpdir}/foo')
    _reset_experiment()

    mlflow_cfg = {
        'experiment_name': 'foo',
        'run_name': 'bar',
        'artifact_location': '/foo/bar',
    }

    with uv.start_run(**mlflow_cfg) as active_run, uv.active_reporter(
        reporter()) as r:
      assert r is not None

      steps = [{'step': 1, 'm': {'a': value,}}]

      for p in steps:
        for k, v in p['m'].items():
          with pytest.raises(ValueError):
            r.report(step=p['step'], k=k, v=v)
