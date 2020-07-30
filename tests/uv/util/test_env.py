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

import os

import uv.util.env as ue


def test_extract_params(monkeypatch):

  def mem_env(prefix):
    return {
        f"{prefix}_MY_KEY": "face",
        f"{prefix}_ANOTHER_KEY": "sandwich",
        f"{prefix}THIRD_KEY": "ham"
    }

  expected = {"my_key": "face", "another_key": "sandwich", "third_key": "ham"}

  # with various prefixes, a custom-supplied environment will return the
  # correctly parsed env variables.
  assert expected == ue.extract_params(prefix="ENVVAR", env=mem_env("ENVVAR"))
  assert expected == ue.extract_params(prefix="funky", env=mem_env("funky"))

  k = f"{ue._ENV_VAR_PREFIX}_RANDOM_KEY"
  v = "better_not_be_set"

  # make sure we don't have some random value set
  if os.environ.get(k):
    monkeypatch.delenv(k)

  # the environment should be empty.
  assert ue.extract_params() == {}

  # set our expected kv pair...
  monkeypatch.setenv(k, v)

  # and get it back from the env.
  assert ue.extract_params() == {"random_key": v}
