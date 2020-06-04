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
"""Tests of the various reporter base implementations, plus combinators."""

import itertools

import pytest
import uv.reporter.base as b
import uv.reporter.store as r


@pytest.fixture
def mem():
  return r.MemoryReporter()


class TestReporter(b.AbstractReporter):

  def report(self, step, k, v):
    return None


def test_default_reporter():
  """By default, `reader` isn't implemented."""

  assert TestReporter().reader() is None

  # close does nothing by default.
  assert TestReporter().close() is None


class ThrowCloseReporter(b.AbstractReporter):

  def close(self) -> None:
    raise IOError("Don't close me!")


def test_prefix_reporter(mem):
  prefixed = mem.with_prefix("toots")
  prefixed_reader = prefixed.reader()
  reader = mem.reader()

  # reporting through a prefixed reporter, through either method, should
  # prepend the prefix onto the key before hitting the underlying store.
  prefixed.report_all(0, {"a": 1, "b": 2})
  prefixed.report(1, "a", 2)

  expected = {"toots.a": [1, 2], "toots.b": [2]}

  # if you read through the base reader, you'll need to prepend the prefix.
  assert reader.read_all(["toots.a", "toots.b"]) == expected
  assert prefixed_reader.read_all(["a", "b"]) == expected

  # check that the close is passthrough:
  with pytest.raises(IOError):
    ThrowCloseReporter().with_prefix("prefix").close()


def test_prefix_reporter_handles_int_keys(mem):
  prefixed = mem.with_prefix("toots")
  prefixed_reader = prefixed.reader()
  reader = mem.reader()

  prefixed.report_all(0, {0: 1, 1: 2})
  prefixed.report_all(0, {"0": 3})
  prefixed.report(1, 0, 2)

  expected = {"toots.0": [1, 3, 2], "toots.1": [2]}

  # if you read through the base reader, you'll need to prepend the prefix.
  assert reader.read_all(["toots.0", "toots.1"]) == expected
  assert prefixed_reader.read_all([0, 1]) == expected


def test_suffix_reporter(mem):
  suffixed = mem.with_suffix("toots")
  suffixed_reader = suffixed.reader()
  reader = mem.reader()

  # reporting through a suffixed reporter, through either method, should
  # prepend the suffix onto the key before hitting the underlying store.
  suffixed.report_all(0, {"a": 1, "b": 2})
  suffixed.report(1, "a", 2)

  expected = {"a.toots": [1, 2], "b.toots": [2]}

  # if you read through the base reader, you'll need to prepend the suffix.
  assert reader.read_all(["a.toots", "b.toots"]) == expected
  assert suffixed_reader.read_all(["a", "b"]) == expected

  # check that the close is passthrough:
  with pytest.raises(IOError):
    ThrowCloseReporter().with_suffix("suffix").close()


class CountCloseReporter(b.AbstractReporter):

  def __init__(self):
    self._closed = 0

  def times_called(self) -> int:
    return self._closed

  def close(self) -> None:
    self._closed += 1


def test_multi_reporter(mem):
  # this compound reporter should 4x add each reported item.
  mem4 = mem.plus(mem, mem, mem)
  reader = mem.reader()

  mem4.report_all(0, {"a": 1})
  mem4.report(1, "b", 2)

  assert reader.read_all(["a", "b"]) == {"a": [1, 1, 1, 1], "b": [2, 2, 2, 2]}

  ccr = CountCloseReporter()
  ccr4 = ccr.plus(ccr, ccr, ccr)
  ccr4.close()

  # the multi-reporter should call the backing store 4 times, since we used
  # copies of the same store.
  assert ccr.times_called() == 4

  # check that the close is passthrough:
  with pytest.raises(IOError):
    ThrowCloseReporter().plus(mem).close()


def test_filter_step(mem):
  on_false = r.MemoryReporter()

  even_only = mem.filter_step(lambda step: step % 2 == 0, on_false=on_false)
  reader = even_only.reader()

  even_only.report(0, "a", 0)
  even_only.report(1, "a", 1)
  even_only.report(2, "a", 2)

  even_only.report_all(3, {"b": 1, "c": 2})
  even_only.report_all(4, {"b": 2, "c": 4})

  # only the items written with even steps above should get through.
  assert reader.read_all(["a", "b", "c"]) == {"a": [0, 2], "b": [2], "c": [4]}

  # every time the predicate returned false, items went into the other store.
  assert on_false.reader().read_all(["a", "b", "c"]) == {
      "a": [1],
      "b": [1],
      "c": [2]
  }

  # check that the close is passthrough:
  with pytest.raises(IOError):
    ThrowCloseReporter().filter_step(lambda step: True).close()


def test_report_each_n():
  mem1 = r.MemoryReporter().report_each_n(-100)
  mem2 = r.MemoryReporter().report_each_n(1)
  even_only = r.MemoryReporter().report_each_n(2)
  reporter = mem1.plus(mem2, even_only)
  even_reader = even_only.reader()

  reporter.report(0, "a", 0)
  reporter.report(1, "a", 1)
  reporter.report(2, "a", 2)

  reporter.report_all(3, {"b": 1, "c": 2})
  reporter.report_all(4, {"b": 2, "c": 4})

  # only the items written with even steps above should get through.
  assert even_reader.read_all(["a", "b", "c"]) == {
      "a": [0, 2],
      "b": [2],
      "c": [4]
  }

  all_data = {"a": [0, 1, 2], "b": [1, 2], "c": [2, 4]}

  # both mem1 and mem2 receive ALL data.
  assert mem1.reader().read_all(["a", "b", "c"]) == all_data
  assert mem2.reader().read_all(["a", "b", "c"]) == all_data


def test_filter_values(mem):
  on_false = r.MemoryReporter()

  step_plus_v_even = mem.filter_values(lambda step, v: (step + v) % 2 == 0,
                                       on_false=on_false)
  reader = step_plus_v_even.reader()

  step_plus_v_even.report(0, "a", 0)
  step_plus_v_even.report(1, "a", 4)
  step_plus_v_even.report(2, "a", 2)
  step_plus_v_even.report(3, "a", 2)

  step_plus_v_even.report_all(3, {"b": 1, "c": 2})
  step_plus_v_even.report_all(4, {"b": 2, "c": 4})

  # only the items written where the step PLUS the value is even above should
  # get through.
  assert reader.read_all(["a", "b", "c"]) == {
      "a": [0, 2],
      "b": [1, 2],
      "c": [4]
  }

  # every time the predicate returned false, items went into the other store.
  assert on_false.reader().read_all(["a", "b", "c"]) == {
      "a": [4, 2],
      "b": [],
      "c": [2]
  }

  # check that the close is passthrough:
  with pytest.raises(IOError):
    ThrowCloseReporter().filter_values(lambda step: True).close()

  # check that the close is passthrough for the on_false reporter:
  with pytest.raises(IOError):
    r.MemoryReporter().filter_values(lambda step: True,
                                     on_false=ThrowCloseReporter()).close()


def test_map_values(mem):
  squared_if_even = mem.map_values(lambda step, v: v * v
                                   if step % 2 == 0 else v)
  reader = mem.reader()

  squared_if_even.report(2, "a", 2)
  squared_if_even.report_all(3, {"b": 1, "c": 7})

  # all of the reported values, when reported through the squared reporter...
  # are squared, IF the step value is even.
  assert reader.read_all(["a", "b", "c", "d"]) == {
      "a": [4],
      "b": [1],
      "c": [7],
      "d": []
  }

  # check that the close is passthrough:
  with pytest.raises(IOError):
    ThrowCloseReporter().map_values(lambda step, v: v).close()


def test_stepped(mem):
  stepped_mem = mem.stepped(step_key="this_step")
  reader = mem.reader()

  stepped_mem.report(2, "a", 2)
  stepped_mem.report_all(3, {"b": 1, "c": 7})

  # a stepped reporter converts the incoming data into a dictionary that logs
  # the step as well as the value.
  assert reader.read_all(["a", "b", "c"]) == {
      "a": [{
          "this_step": 2,
          "value": 2
      }],
      "b": [{
          "this_step": 3,
          "value": 1
      }],
      "c": [{
          "this_step": 3,
          "value": 7
      }],
  }


def test_from_thunk(mem):
  counter = itertools.count()

  def thunk():
    return {"counter": next(counter)}

  thunked = mem.from_thunk(thunk)
  reader = thunked.reader()

  # every time thunk(step) gets called, the function above returns a new input
  # to report_all with the supplied step.
  thunked.thunk(0)

  # report and report_all pass through.
  thunked.report(1, "a", 2)
  thunked.thunk(2)
  thunked.report_all(3, {"b": 1, "c": 7})
  thunked.thunk(4)

  assert reader.read_all(["a", "b", "c", "counter"]) == {
      "a": [2],
      "b": [1],
      "c": [7],
      "counter": [0, 1, 2]
  }

  # check that the close is passthrough:
  with pytest.raises(IOError):
    ThrowCloseReporter().from_thunk(lambda: 10).close()
