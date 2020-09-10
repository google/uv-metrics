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
"""Tests for the prefix utilities."""

import pytest
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


@given(st.dictionaries(st.text(min_size=1), st.integers()))
def test_flatten_flat(m):
  # Tests that flattening does not affect dictionaries which are already flat
  flattened = a.flatten(m)

  assert flattened == m


@given(
    st.dictionaries(st.text(min_size=1),
                    st.dictionaries(st.text(min_size=1), st.integers())))
def test_flatten_idempotence(m):
  # Tests that flattening a dictionary twice does the same thing as
  # flattening it once, i.e. the flattening operation is idempotent
  assert a.flatten(m) == a.flatten(a.flatten(m))


@given(
    st.dictionaries(st.text(min_size=1),
                    st.dictionaries(st.text(min_size=1), st.integers())))
def test_flatten_notflat(m):
  # Tests that flattening properly handles dictionaries which are not flat
  flattened = a.flatten(m)

  for k, vs in m.items():
    for v_k, v_vs in vs.items():
      assert flattened[k + '.' + v_k] == v_vs


@given(
    st.dictionaries(st.text(min_size=1),
                    st.dictionaries(st.text(min_size=1),
                                    st.integers(),
                                    min_size=1),
                    min_size=1))
def test_flatten_error(m):
  # Tests that flattening returns an error when it is given dictionaries
  # which would have a key collision after flattening

  k = list(m.keys())[0]
  k_1 = list(m[k].keys())[0]
  collision_key = k + '.' + k_1
  m.update({collision_key: "ANYTHING"})

  with pytest.raises(ValueError):
    flattened = a.flatten(m)
