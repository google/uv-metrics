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
"""Tests of the various reporter store implementations."""

from collections import OrderedDict
import hypothesis.strategies as st
import numpy as np
from hypothesis import given

import pytest
import tests.uv.util.test_init as ti
import uv.reporter.store as rs


@given(st.dictionaries(st.text(min_size=1), st.integers()))
def test_lambda_reporter(m):

  # once we push all values into the store we expect metric => singleton.
  wrapped = {k: [v] for k, v in m.items()}
  double_wrapped = {k: [v, v] for k, v in m.items()}

  # make a memory reporter and a paired reader.
  mem = rs.MemoryReporter()
  reader = mem.reader()

  # these lambda reporters write to the backing memory store.
  r_reporter = rs.LambdaReporter(report=mem.report)
  ra_reporter = rs.LambdaReporter(report_all=mem.report_all)

  # report it ALL and check that everything made it in.
  ra_reporter.report_all(0, m)
  assert reader.read_all(m.keys()) == wrapped

  # now use ra_reporter's report method, which should delegate to report_all:
  for k, v in m.items():
    ra_reporter.report(0, k, v)

  # now we should have two copies for each key.
  assert reader.read_all(m.keys()) == double_wrapped

  # clear and confirm that everything is empty:
  mem.clear()
  assert reader.read_all(m.keys()) == {k: [] for k in m.keys()}

  # do the same thing again, but using the report interface this time.
  for k, v in m.items():
    r_reporter.report(0, k, v)

  assert reader.read_all(m.keys()) == wrapped

  # same thing as before, we check the report_all implementation when we only
  # supply a report function.
  r_reporter.report_all(0, m)
  assert reader.read_all(m.keys()) == double_wrapped


def test_lambda_reporter_errors():
  """The close function works, and you have to supply all required args."""

  # You have to supply a report or report_all fn.
  with pytest.raises(ValueError):
    rs.LambdaReporter()

  def explode():
    raise IOError("Don't close me!")

  report = rs.LambdaReporter(report=lambda _: None, close=explode)

  with pytest.raises(IOError):
    report.close()


def test_logging_reporter():
  """Check that the LoggingReporter actually logs out properly."""
  mem = ti.MemFile()

  reporter = rs.LoggingReporter(file=mem)

  # reporter handles non-native types like float32 just fine.
  reporter.report(0, "a", np.float32(1))

  # compound logging.
  m = OrderedDict([("a", 2), ("b", "cake")])
  reporter.report_all(1, m)

  # all items have been logged out.
  assert mem.items() == [
      'Step 0: a = 1.000', '\n', 'Step 1: a = 2.000, b = cake', '\n'
  ]


def test_logging_reporter_types():
  mem = ti.MemFile()
  reporter = rs.LoggingReporter(file=mem)

  v = np.array([1, 2, 3])
  reporter.report(0, "a", v)
  assert mem.items() == ['Step 0: a = {}'.format(str(v)), '\n']


def test_memory_reporter_types():
  # make a memory reporter and a paired reader.
  mem = rs.MemoryReporter()
  reader = mem.reader()

  # reporting to 1 and "1" should do the same thing.
  mem.report_all(0, {1: "face"})
  mem.report_all(1, {"1": "cake"})

  # int and string that stringify to the same key should return the values.
  assert reader.read(1) == ["face", "cake"]
  assert reader.read("1") == reader.read(1)
