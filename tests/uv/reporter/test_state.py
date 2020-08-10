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
import pprint as pp
import uv
import uv.reporter.state as s
import uv.reporter.store as r
import tempfile


def test_global_reporter():
  r1 = r.MemoryReporter()
  reader1 = r1.reader()

  r2 = r.MemoryReporter()
  reader2 = r2.reader()

  r3 = r.MemoryReporter()
  reader3 = r3.reader()

  # By default, we get the null reporter and nothing happens.
  assert s.report(1, "face", 2) is None
  assert s.report_all(2, {"face": 2, "cake": 3}) is None

  s.set_reporter(r1)

  # boom!
  assert s.get_reporter() == r1

  # Now, reports go into the global reporter.
  s.report(1, "face", 2)
  s.report_all(2, {"face": 2, "cake": 3})

  # confirm:
  assert reader1.read("face") == [2, 2]
  assert reader1.read_all(["face", "cake"]) == {"face": [2, 2], "cake": [3]}

  # params are correctly reported.
  s.report_param("key_for_me", "value")
  s.report_params({"k": "v", "k2": "v2"})
  assert r1._params == {"key_for_me": "value", "k": "v", "k2": "v2"}

  with s.active_reporter(r2):

    # params get reported to the proper reporter.
    s.report_param("key", "value")
    assert r1._params == {"key_for_me": "value", "k": "v", "k2": "v2"}
    assert r2._params == {"key": "value"}

    # These report go through to r2, not r1.
    s.report(1, "hammer", 2)
    s.report_all(1, {"steve": 2, "john": 3})

    assert reader1.read_all(["hammer", "steve", "john"]) == {
        "hammer": [],
        "john": [],
        "steve": []
    }

    assert reader2.read_all(["hammer", "steve", "john"]) == {
        "hammer": [2],
        "john": [3],
        "steve": [2]
    }

    # these can nest:
    with s.active_reporter(r3):
      s.report(4, "deeper", 10)

      assert reader2.read("deeper") == []
      assert reader3.read("deeper") == [10]

    # when you leave a block, you hit the next reporter back.
    s.report(4, "deeper", 12)
    assert reader2.read("deeper") == [12]
    assert reader3.read("deeper") == [10]


def test_start_run(monkeypatch):

  with tempfile.TemporaryDirectory() as tmpdir:

    mlf.set_tracking_uri(f'file:{tmpdir}/foo')

    # no run should be active initially
    assert mlf.active_run() is None

    # test default args
    with uv.start_run() as r:
      active_run = mlf.active_run()
      assert active_run is not None
      assert active_run == r

    # test explicit experiment name, run name, artifact location
    cfg = {
        'experiment_name': 'foo',
        'run_name': 'bar',
        'artifact_location': 'gs://foo/bar',
    }

    with uv.start_run(**cfg) as r:
      active_run = mlf.active_run()
      assert active_run is not None
      assert active_run == r

      assert r.data.tags['mlflow.runName'] == cfg['run_name']
      assert mlf.get_experiment_by_name(cfg['experiment_name']) is not None
      assert mlf.get_artifact_uri().startswith(cfg['artifact_location'])

    # test env var experiment name, run name, artifact location
    cfg = {
        'MLFLOW_EXPERIMENT_NAME': 'env_foo',
        'MLFLOW_RUN_NAME': 'env_bar',
        'MLFLOW_ARTIFACT_ROOT': 'gs://env/foo/bar'
    }

    for k, v in cfg.items():
      monkeypatch.setenv(k, v)

    with uv.start_run() as r:
      active_run = mlf.active_run()
      assert active_run is not None
      assert active_run == r

      assert r.data.tags['mlflow.runName'] == cfg['MLFLOW_RUN_NAME']
      assert mlf.get_experiment_by_name(
          cfg['MLFLOW_EXPERIMENT_NAME']) is not None
      assert mlf.get_artifact_uri().startswith(cfg['MLFLOW_ARTIFACT_ROOT'])

    for k, v in cfg.items():
      monkeypatch.delenv(k)

    # test env var tags
    cfg = {
        'tag0': 'foo',
        'tag1': 'bar',
    }

    for k, v in cfg.items():
      monkeypatch.setenv(f'ENVVAR_{k}', v)

    with uv.start_run() as r:
      client = mlf.tracking.MlflowClient()
      tags = client.get_run(r.info.run_id).data.tags
      for k, v in cfg.items():
        assert k in tags, pp.pformat(tags)
        assert tags[k] == v, pp.pformat(tags)

    for k in cfg:
      monkeypatch.delenv(f'ENVVAR_{k}')

    # test CAIP tags
    monkeypatch.setenv('CLOUD_ML_JOB_ID', 'foo_cloud_job')

    with uv.start_run() as r:
      client = mlf.tracking.MlflowClient()
      tags = client.get_run(r.info.run_id).data.tags
      assert 'cloud_ml_job_details' in tags, pp.pformat(tags)
      assert tags['cloud_ml_job_details'] == (
          'https://console.cloud.google.com/ai-platform/jobs/foo_cloud_job')

      assert 'cloud_ml_job_id' in tags, pp.pformat(tags)
      assert tags['cloud_ml_job_id'] == 'foo_cloud_job'

    monkeypatch.delenv('CLOUD_ML_JOB_ID')
