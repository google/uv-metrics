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
"""Utilities grab bag."""

import datetime
import json
from functools import singledispatch
from typing import Any, List

import numpy as np
import tqdm


def to_metric(v: Any) -> float:
  """Converts the incoming item into something we can log.
  """
  if hasattr(v, 'numpy'):
    return v.numpy()

  return v


@singledispatch
def to_serializable(val):
  """Used by default."""

  if hasattr(val, 'numpy'):
    return val.numpy()

  return str(val)


@to_serializable.register(np.floating)
def ts_np_floating(val):
  """Used if *val* is an instance of numpy.floating."""
  return float(val)


@to_serializable.register(np.integer)
def ts_np_int(val):
  """Used if *val* is an instance of numpy.integer."""
  return int(val)


@to_serializable.register(np.ndarray)
def ts_np_array(val):
  """Convert a numpy array to a serializable list."""
  return val.tolist()


def json_str(item: Any) -> str:
  """Converts the supplied python object to a Python dictionary.

  The difference from json.dumps is that this method makes a best effort to
  serialize anything it finds within a nested structure. np.float32 instances,
  for example.

  """
  return json.dumps(item, default=to_serializable)


def uuid():  # pragma: no cover
  """Generates a sane UUID for use in test files and metric directories."""
  return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def wrap(item: Any) -> List[Any]:
  """Ensures that the input is either a list, or wrapped in a list. Returns []
  for None.

  """
  if item is None:
    return []

  if isinstance(item, list):
    return item

  return [item]


def is_number(s):
  """Returns true if the supplied item can be converted into a float; false
  otherwise.

  """
  try:
    float(s)
    return True
  except Exception:
    return False


class TqdmFile():
  """Dummy file-like that will write to tqdm's 'write' method, which will in turn
  write back into the supplied file. Use this when you need to redirect some
  stream in such a way that won't cause the tqdm progress bar to reset.

  """
  file = None

  def __init__(self, file):
    self.file = file

  def write(self, x):
    if len(x.rstrip()) > 0:
      tqdm.tqdm.write(x, file=self.file, nolock=False)

  def flush(self):
    return getattr(self.file, "flush", lambda: None)()

  def isatty(self):
    return getattr(self.file, "isatty", lambda: False)()
