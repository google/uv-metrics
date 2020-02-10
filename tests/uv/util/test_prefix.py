"""Tests for the prefix utilities."""

import hypothesis.strategies as st
from hypothesis import given

import uv.util.prefix as p


@given(st.dictionaries(st.text(min_size=1), st.integers()))
def test_by_prefix(m):
  wrapped = p.by_prefix({"test": m, "train": m})

  for k, vs in m.items():
    assert wrapped.get(p.attach_s(k, "test")) == vs
    assert wrapped.get(p.attach_s(k, "train")) == vs
    assert wrapped.get(p.attach_s(k, "random")) is None
