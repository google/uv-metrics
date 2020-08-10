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
"""AbstractReporter implementations that live at the bottom of the reporter
stack. These reporters aren't combinators; they're responsible for persisting
metrics into underlying store or mechanism.

"""

import sys
from typing import Callable, Dict, List, Optional

import uv.reader.base as rb
import uv.reader.store as rs
import uv.types as t
import uv.util as u
from uv.reporter.base import AbstractReporter

# Class Definitions


class NullReporter(AbstractReporter):
  """Reporter that does nothing with the metrics passed to its various methods.
  reader() returns an instance of rs.EmptyReader.

  """

  def report_all(self, step, m):
    return None

  def report(self, step, k, v):
    return None

  def reader(self) -> Optional[rb.AbstractReader]:
    return rs.EmptyReader()


class LambdaReporter(AbstractReporter):
  """AbstractReporter implementation that defers to a supplied lambda for its
  persistence ability. This allows you to escape the object-oriented
  programming paradigm, if you so choose.

  Args:
    report: Function called whenever reporter.report(step, k, v) is called.
    report_all: Function called whenever reporter.report_all(step, m) is
                called.
    report_param: Function called whenever reporter.report_param(k, v) is
                  called.
    report_params: Function called whenever reporter.report_params(m) is
                   called.
    close: If supplied, this no-arg function will get called by this instance's
           `close` method.

  """

  def __init__(self,
               report: Optional[Callable[[int, t.MetricKey, t.Metric],
                                         None]] = None,
               report_all: Optional[Callable[[int, Dict[t.MetricKey, t.Metric]],
                                             None]] = None,
               report_param: Optional[Callable[[str, str], None]] = None,
               report_params: Optional[Callable[[Dict[str, str]], None]] = None,
               close: Optional[Callable[[], None]] = None):
    if report is None and report_all is None:
      raise ValueError(
          "Must supply one of `report` and `report_all` to `LambdaReporter`.")

    self._reportparam = report_param
    self._reportparams = report_params
    self._report = report
    self._reportall = report_all
    self._close = close

  def report_param(self, k: str, v: str) -> None:
    if self._reportparam is None:
      super().report_param(k, v)
    else:
      self._reportparam(k, v)

  def report_params(self, m: Dict[str, str]) -> None:
    if self._reportparams is None:
      super().report_params(m)
    else:
      self._reportparams(m)

  def report_all(self, step, m):
    if self._reportall is None:
      super().report_all(step, m)
    else:
      self._reportall(step, m)

  def report(self, step, k, v):
    if self._report is None:
      super().report(step, k, v)
    else:
      self._report(step, k, v)

  def close(self) -> None:
    if self._close is not None:
      self._close()


class LoggingReporter(AbstractReporter):
  """Reporter that logs all data to the file handle you pass in using a fairly
  sane format. Compatible with tqdm, the python progress bar.

  """

  @staticmethod
  def tqdm():  # pragma: no cover
    """Returns a logging reporter that will work with a tqdm progress bar."""
    return LoggingReporter(u.TqdmFile(sys.stderr))

  def __init__(self, file=sys.stdout, digits: int = 3):

    self._file = file
    self._digits = digits

  def _format(self, v: t.Metric) -> str:
    """Formats the value into something appropriate for logging."""
    if u.is_number(v):
      return "{num:.{digits}f}".format(num=float(v), digits=self._digits)

    return str(v)

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    s = ", ".join(["{} = {}".format(k, self._format(v)) for k, v in m.items()])
    f = self._file
    print("Step {}: {}".format(step, s), file=f)


class MemoryReporter(AbstractReporter):
  """Reporter that stores metrics in a Python dictionary, keyed by t.MetricKey.
  Metrics are stored as a list.

  Args:
    m: Optional dictionary mapping metric keys to a list of accumulated metric
       values. If supplied, this dictionary will be mutated as new metrics
       arrive.

  """

  def __init__(self,
               m: Optional[Dict[str, List[t.Metric]]] = None,
               params_store: Optional[Dict[str, str]] = None):
    if m is None:
      m = {}

    if params_store is None:
      params_store = {}

    self._m = m
    self._params = params_store

  def report_param(self, k: str, v: str) -> None:
    self._params[k] = v

  def report_params(self, m: Dict[str, str]) -> None:
    self._params.update({**m})

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    for k, v in m.items():
      self._m.setdefault(str(k), []).append(v)

  def clear(self):
    """Erase all key-value pairs in the backing store."""
    self._m.clear()

  def reader(self) -> Optional[rb.AbstractReader]:
    return rs.MemoryReader(self._m)
