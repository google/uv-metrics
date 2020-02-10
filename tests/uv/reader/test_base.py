"""Tests of the base reader and combinators."""

from typing import Dict, List

import hypothesis.strategies as st
from hypothesis import given

import pytest
import uv.reader.base as b
import uv.reader.store as rs
import uv.types as t
import uv.util.prefix as p


class JustRead(b.AbstractReader):
  """Class that ONLY overrides read, not read_all."""

  def __init__(self, base: b.AbstractReader):
    self._base = base

  def read(self, k: str) -> List[t.Metric]:
    return self._base.read(k)


class JustReadAll(b.AbstractReader):
  """Class that ONLY overrides read_all, not read."""

  def __init__(self, base: b.AbstractReader):
    self._base = base

  def read_all(self, ks: List[str]) -> Dict[str, List[t.Metric]]:
    return self._base.read_all(ks)


@given(
    st.dictionaries(st.text(min_size=1),
                    st.lists(st.integers(), max_size=100),
                    max_size=100))
def test_default_read_implementations(m):
  """Check that the read and read_all implementation that, by default, call each
  other, actually work.

  """
  mem = rs.MemoryReader(m)
  just_read = JustRead(mem)
  just_read_all = JustReadAll(mem)

  ks = m.keys()
  just_read_results = just_read.read_all(ks)
  assert just_read_results == just_read_all.read_all(ks)
  assert just_read_results == m

  for k in ks:
    just_read_results = just_read.read(k)
    assert just_read_results == just_read_all.read(k)
    assert just_read_results == m[k]

  assert just_read.close() is None


@given(st.text(min_size=1),
       st.dictionaries(st.text(min_size=1),
                       st.lists(st.integers(), max_size=100),
                       max_size=100))
def test_prefixed_reader(prefix, m):
  """Test that prefixes work."""
  prefixed = {p.attach_s(k, prefix): v for k, v in m.items()}
  mem = rs.MemoryReader(prefixed)

  # the bare store, when queried with keys with the prefix attached, returns
  # the right stuff.
  assert mem.read_all(prefixed.keys()) == prefixed

  reader = mem.with_prefix(prefix)
  # If instead you generate a new reader using with_prefix, you don't need to
  # pass prefixed keys in to read_all; they'll get automatically attached.
  assert reader.read_all(m.keys()) == prefixed

  # read implementation works too.
  for k, v in m.items():
    assert reader.read(k) == v


class ThrowCloseReader(b.AbstractReader):

  def close(self) -> None:
    raise IOError("Don't close me!")


def check_passthrough_close(base_to_reader_fn):
  """Takes a function from a base to reader, and checks that calling close on the
  returned reader actually passes through to the base.

  """
  with pytest.raises(IOError):
    base = ThrowCloseReader()
    base_to_reader_fn(base).close()


def test_prefixed_reader_passthrough_close():
  check_passthrough_close(lambda s: b.PrefixedReader(s, prefix='face'))
