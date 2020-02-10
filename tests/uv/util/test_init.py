"""Tests for the functions that live in the __init__.py file."""

import json

import hypothesis.strategies as st
import numpy as np
from hypothesis import given

import pytest
import uv.util as u


class Wrapper():
  """Wrapper class that has a numpy method, for testing."""

  def __init__(self, x):
    self._x = x

  def numpy(self):
    """Using this instead of importing tensorflow..."""
    return np.float64(self._x)


def test_to_metric():
  x = Wrapper(100)
  assert u.to_metric(100) == 100
  assert u.to_metric(x) == np.float64(100)


def test_to_serializable():
  """Check that various non-serializable things can in fact be serialized using
  this dispatch method."""
  f = 100.0

  # json can't serialize float32:
  with pytest.raises(TypeError):
    json.dumps(np.float32(f))

  # but it can here, if we pass it through to_serializable.
  assert json.dumps(u.to_serializable(np.float32(f))) == str(f)

  # this passthrough automatically using u.json_str.
  assert u.json_str(f) == str(f)

  # by default, to make something serializable, turn it into a string.
  assert u.to_serializable("face") == "face"


def test_wrap():
  """Test the best-effort wrapping of non-lists."""

  assert u.wrap([1]) == [1]
  assert u.wrap(1) == [1]
  assert u.wrap(None) == []
  assert u.wrap((1, 2)) == [(1, 2)]


def test_is_number():
  """This is meant to check if something can be emitted as a number via json."""
  assert u.is_number("100")
  assert u.is_number(np.float32(100))
  assert u.is_number(np.float64(100))
  assert not u.is_number("face")


class MemFile():
  """Dummy file-like that will write to a list."""

  def __init__(self):
    self._l = []

  def items(self):
    return self._l

  def write(self, x):
    self._l.append(x)

  def flush(self):
    raise IOError("NO FLUSH!")

  def isatty(self):
    raise IOError("NO ATTY!")


@given(st.lists(st.text(min_size=1)))
def test_tqdm_file(lines):
  """Test properties of the TQDM logger - check that it properly passes through
  Tqdm.

  """
  mem = MemFile()
  f = u.TqdmFile(file=mem)

  for l in lines:
    f.write(l)

  def strip(items):
    return [l for l in items if len(l.rstrip()) > 0]

  assert strip(mem.items()) == strip(lines)

  # test passthroughs:
  with pytest.raises(IOError):
    f.flush()

  with pytest.raises(IOError):
    f.isatty()
