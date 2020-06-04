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
"""AbstractReader implementations that live at the bottom of the reader stack.
These readers aren't combinators; they're responsible for returning stored
values from some underlying store or mechanism.

"""

from typing import Callable, Dict, Iterable, List, Optional

import uv.types as t
from uv.reader.base import AbstractReader, IterableReader


class EmptyReader(AbstractReader, IterableReader):
  """AbstractReader that uses NO internal state. EmptyReader returns an empty
  list for every metric.

  """

  def keys(self) -> Iterable[t.MetricKey]:
    return []

  def read_all(self,
               ks: List[t.MetricKey]) -> Dict[t.MetricKey, List[t.Metric]]:
    return {k: [] for k in ks}

  def read(self, k: t.MetricKey) -> List[t.Metric]:
    return []


class LambdaReader(AbstractReader):
  """AbstractReader implementation that defers to a supplied lambda for its
  values. This allows you to escape the object-oriented programming paradigm,
  if you so choose.

  Args:
    read: Function called whenever reader.read(k) is called.
    read_all: Function called whenever reader.read_all(ks) is called.
    close: If supplied, this no-arg function will get called by this instance's
           `close` method.

  """

  def __init__(self,
               read: Optional[Callable[[t.MetricKey], List[t.Metric]]] = None,
               read_all: Optional[Callable[[List[t.MetricKey]],
                                           Dict[t.MetricKey,
                                                List[t.Metric]]]] = None,
               close: Optional[Callable[[], None]] = None):
    if read is None and read_all is None:
      raise ValueError(
          "Must supply one of `read` and `read_all` to `LambdaReader`.")

    self._read = read
    self._readall = read_all
    self._close = close

  def read_all(self,
               ks: List[t.MetricKey]) -> Dict[t.MetricKey, List[t.Metric]]:
    if self._readall is None:
      return super().read_all(ks)

    return self._readall(ks)

  def read(self, k: t.MetricKey) -> List[t.Metric]:
    if self._read is None:
      return super().read(k)

    return self._read(k)

  def close(self) -> None:
    if self._close is not None:
      self._close()


class MemoryReader(AbstractReader, IterableReader):
  """Reader that queries the supplied dictionary for values.

  Args:
    m: Dictionary mapping metric keys to a list of accumulated metric values.

  """

  def __init__(self, m: Optional[Dict[str, List[t.Metric]]]):
    if m is None:
      m = {}

    self._m = m

  def keys(self) -> Iterable[t.Metric]:
    return self._m.keys()

  def read_all(self,
               ks: List[t.MetricKey]) -> Dict[t.MetricKey, List[t.Metric]]:
    return {str(k): self._m.get(str(k), []) for k in ks}

  def read(self, k: t.MetricKey) -> List[t.Metric]:
    return self._m.get(str(k), [])
