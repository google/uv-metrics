"""Tests for the prefix utilities."""

import hypothesis.strategies as st
from hypothesis import given

import uv.util.attachment as a


@given(st.dictionaries(st.text(min_size=1), st.integers()))
def test_by_prefix(m):
  wrapped = a.by_prefix({"test": m, "train": m})

  for k, vs in m.items():
    assert wrapped.get(a.attach_s(k, "test")) == vs
    assert wrapped.get(a.attach_s(k, "train")) == vs
    assert wrapped.get(a.attach_s(k, "random")) is None


@given(st.dictionaries(st.text(min_size=1), st.integers()))
def test_by_suffix(m):
  wrapped = a.by_suffix({"test": m, "train": m})

  for k, vs in m.items():
    assert wrapped.get(a.attach_s(k, "test", prefix=False)) == vs
    assert wrapped.get(a.attach_s(k, "train", prefix=False)) == vs
    assert wrapped.get(a.attach_s(k, "random", prefix=False)) is None
