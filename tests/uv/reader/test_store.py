"""Tests of the various reader store implementations."""

import hypothesis.strategies as st
from hypothesis import given

import pytest
import uv.reader.store as s
import uv.reporter.store as rs


@given(st.integers(min_value=0),
       st.dictionaries(st.text(min_size=1), st.integers()))
def test_memory_rt(step, m):
  """Check that any values pushed into a store are recovered."""
  mem = rs.MemoryReporter().stepped()
  reader = mem.reader()

  mem.report_all(step, m)

  expected = {k: [{"step": step, "value": v}] for k, v in m.items()}
  assert reader.read_all(m.keys()) == expected


@given(st.sets(st.text(min_size=1)))
def test_memory_empty(ks):
  """An empty reader should return nothing ever."""
  reader = s.MemoryReader({})
  assert reader.read_all(ks) == {k: [] for k in ks}

  # similar result if you don't supply ANY map.
  assert s.MemoryReader(m=None).read_all(ks) == {k: [] for k in ks}

  # same works for read implementation:
  for k in ks:
    assert reader.read(k) == []


@given(st.text(min_size=1), st.lists(st.floats()))
def test_timeseries_all_ends_up_in_memory(k, vs):
  """Check that if many items are passed in for the same key, they'll all end up
  in memory in order.

  """
  mem = rs.MemoryReporter().stepped()
  reader = mem.reader()

  for i, v in enumerate(vs):
    mem.report(i, k, v)

  expected = [{"step": i, "value": v} for i, v in enumerate(vs)]
  assert reader.read(k) == expected


def test_memory_unit():
  """Non-hypothesis version to give a clear example."""
  mem = rs.MemoryReporter().stepped()
  reader = mem.reader()

  mem.report_all(0, {"a": 1, "b": 2})

  assert reader.read("a") == [{"step": 0, "value": 1}]
  assert reader.read("gunk") == []


@given(
    st.lists(st.dictionaries(st.text(min_size=1), st.integers(), max_size=100),
             max_size=10))
def test_null_empty(input_dicts):
  """An empty reader should return nothing ever."""

  null = rs.NullReporter()
  reader = null.reader()

  for i, m in enumerate(input_dicts):
    null.report_all(i, m)

    # let's report too, for good measure.
    for k, v in m.items():
      null.report(i, k, v)

  for m in input_dicts:
    ks = m.keys()
    assert reader.read_all(ks) == {k: [] for k in ks}

    # same for read:
    for k in ks:
      assert reader.read(k) == []


@given(st.sets(st.text(min_size=1)))
def test_lambda_reader(ks):

  def _wrap_all(items):
    return {k: [k] for k in items}

  wrapped = _wrap_all(ks)

  # get a reader that returns a singleton value - just the requested key.
  reader = s.LambdaReader(read=lambda k: [k])
  ra = s.LambdaReader(read_all=_wrap_all)

  assert reader.read_all(ks) == wrapped
  assert ra.read_all(ks) == wrapped

  # Same test, but checking items one at a time.
  for k in ks:
    assert reader.read(k) == [k]
    assert ra.read(k) == [k]


def test_lambda_reader_errors():
  """The close function works, and you have to supply all required args."""

  # You have to supply a read or read_all fn.
  with pytest.raises(ValueError):
    read = s.LambdaReader()

  def explode():
    raise IOError("Don't close me!")

  read = s.LambdaReader(read=lambda k: [], close=explode)

  with pytest.raises(IOError):
    read.close()
