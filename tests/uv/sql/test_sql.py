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
"""Tests for the SQL reader and reporter."""

import time
from contextlib import closing

import uv.sql.reporter as sr
import uv.sql.util as u

import pytest


def test_sqlite_file_exists(tmp_path):
  engine = u.sqlite_engine(str(tmp_path))

  # This is a temp URL, so nothing should exist at that location.
  assert not u.sqlite_file_exists(engine)
  assert not u.sqlite_file_exists(engine.url)

  # then we create the tables...
  sr.create_tables(engine)

  # now the database exists.
  assert u.sqlite_file_exists(engine)
  assert u.sqlite_file_exists(engine.url)

  # db suffix is automatically added:
  assert str(engine.url) == f"sqlite:///{tmp_path}.db"

  # If we explicitly add the suffix, the DB already exists.
  assert u.sqlite_file_exists(u.sqlite_engine(f"{tmp_path}.db"))


def test_rep_string():
  """Check that the custom representation string works for both of our types."""
  metric = sr.Metric(id=10, step=1)

  assert "id='10'" in str(metric)
  assert "step='1'" in str(metric)
  assert "value='None'" in str(metric)

  metric = sr.Experiment(id=10)
  assert "id='10'" in str(metric)
  assert "params='None'" in str(metric)


def test_of_sql_roundtrip(tmp_path):
  engine = u.sqlite_engine(str(tmp_path))

  # you can't make a reporter with an engine pointing to a nonexistent DB:
  with pytest.raises(Exception):
    sr.SQLReporter(engine, sr.Experiment(id=10), 0)

  # Same goes for reader.
  with pytest.raises(Exception):
    sr.SQLReader(engine, sr.Experiment(id=10), 0)

  sr.create_tables(engine)
  experiment = sr.new_experiment(engine, {"learning_rate": 0.01})

  with closing(sr.SQLReporter(engine, experiment, 0)) as reporter:
    with closing(reporter.reader()) as reader:
      with closing(sr.SQLReader(engine, experiment, 0)) as reader2:

        time.sleep(1)
        reporter.report_all(0, {"a": 1})
        reporter.report_all(1, {"a": 2, "b": 3})
        reporter.report_all(2, {"b": 4})

        a_entries = [{"step": 0, "value": 1.0}, {"step": 1, "value": 2.0}]
        b_entries = [{"step": 1, "value": 3.0}, {"step": 2, "value": 4.0}]

        assert list(reader.keys()) == ["a", "b"]
        assert reader.read("a") == a_entries
        assert reader.read("b") == b_entries

        assert reader.read_all(["a", "b"]) == {"a": a_entries, "b": b_entries}

        # Opening a reader directly has the same effect as calling reader() on
        # the reporter.
        assert reader.read_all(["a", "b"]) == reader2.read_all(["a", "b"])

        # Checking for a key that doesn't exist returns an empty list.
        assert reader.read("face") == []
