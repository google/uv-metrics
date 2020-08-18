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

import mlflow as mlf
import tempfile

import uv
from uv.mlflow.reporter import MLFlowReporter


def _reset_experiment():
  # this is needed because the active experiment in mlflow is sticky, so if
  # an earlier test sets this, then things fail here when we don't use
  # an explicit experiment
  mlf.set_experiment(mlf.entities.Experiment.DEFAULT_EXPERIMENT_NAME)


def test_report_params():
  with tempfile.TemporaryDirectory() as tmpdir:
    mlf.set_tracking_uri(f'file:{tmpdir}/foo')
    _reset_experiment()

    mlflow_cfg = {
        'experiment_name': 'foo',
        'run_name': 'bar',
        'artifact_location': 'gs://foo/bar',
    }

    with uv.start_run(**mlflow_cfg) as active_run, uv.active_reporter(
        MLFlowReporter()) as r:
      assert r is not None

      params = {'a': 3, 'b': 'string_param'}
      r.report_params(params)

      assert mlf.active_run() == active_run

      # we need to access the run via a client to inspect most params/tags/metrics
      client = mlf.tracking.MlflowClient()
      run = client.get_run(active_run.info.run_id)
      assert run is not None

      for k, v in params.items():
        p = run.data.params
        assert k in p
        assert p[k] == str(v)


def test_report_param():
  with tempfile.TemporaryDirectory() as tmpdir:
    mlf.set_tracking_uri(f'file:{tmpdir}/foo')
    _reset_experiment()

    mlflow_cfg = {
        'experiment_name': 'foo',
        'run_name': 'bar',
        'artifact_location': 'gs://foo/bar',
    }

    with uv.start_run(**mlflow_cfg) as active_run, uv.active_reporter(
        MLFlowReporter()) as r:
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


def test_report_all():
  with tempfile.TemporaryDirectory() as tmpdir:
    mlf.set_tracking_uri(f'file:{tmpdir}/foo')
    _reset_experiment()

    mlflow_cfg = {
        'experiment_name': 'foo',
        'run_name': 'bar',
        'artifact_location': 'gs://foo/bar',
    }

    with uv.start_run(**mlflow_cfg) as active_run, uv.active_reporter(
        MLFlowReporter()) as r:
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
        assert k in metrics
        metric_data[k] = {
            x.step: x.value
            for x in client.get_metric_history(active_run.info.run_id, k)
        }

      for s in steps:
        cur_step = s['step']
        for k, v in s['m'].items():
          assert metric_data[k][cur_step] == v


def test_report():
  with tempfile.TemporaryDirectory() as tmpdir:
    mlf.set_tracking_uri(f'file:{tmpdir}/foo')
    _reset_experiment()

    mlflow_cfg = {
        'experiment_name': 'foo',
        'run_name': 'bar',
        'artifact_location': 'gs://foo/bar',
    }

    with uv.start_run(**mlflow_cfg) as active_run, uv.active_reporter(
        MLFlowReporter()) as r:
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
