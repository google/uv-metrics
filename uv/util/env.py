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
"""Utilities for interacting with the system environment."""

import os
from typing import Dict, Optional

_ENV_VAR_PREFIX = "ENVVAR"


def extract_params(prefix: Optional[str] = None,
                   env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
  """Some libraries that interact with UV pass experiment parameters via
  environment variables. This function returns a dict containing all
  environment keys (and their values) that begin with the supplied prefix and,
  optionally, an underscore.

  An environment like this:

  ENVVAR_MY_KEY=face
  ENVVAR_ANOTHER_KEY=sandwich
  ENVVARTHIRD_KEY=ham

  would return:

  {
    "my_key": "face",
    "another_key": "sandwich",
    "third_key": "ham"
  }

  """
  if prefix is None:
    prefix = _ENV_VAR_PREFIX

  if env is None:
    env = os.environ

  def relevant():
    for k, v in env.items():
      if k.startswith(prefix):
        stripped = k[len(prefix):].lstrip("_")
        yield stripped.lower(), v

  return dict(relevant())
