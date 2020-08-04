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
"""Tests for the Tensorboard reporter."""

import os
from contextlib import closing
from typing import Any, Dict, Iterable

from tensorflow.core.util import event_pb2
from tensorflow.python.framework import tensor_util
from tensorflow.python.lib.io import tf_record
from tensorflow.python.platform import gfile

import uv.tensorflow.reporter as r


def events_from_file(filepath: str):
  """Returns all events in a single event file.

  Args:
    filepath: Path to the event file.
  Returns:
    A list of all tf.Event protos in the event file.
  """
  records = list(tf_record.tf_record_iterator(filepath))
  result = []
  for rec in records:
    event = event_pb2.Event()
    event.ParseFromString(rec)
    result.append(event)
  return result


def events_from_logdir(log_dir: str):
  """Returns all events in the single eventfile in logdir.

  Args:
    logdir: The directory in which the single event file is sought.
  Returns:
    A list of all tf.Event protos from the single event file.
  Raises:
    AssertionError: If logdir does not contain exactly one file.

  """
  assert gfile.Exists(log_dir)
  files = gfile.ListDirectory(log_dir)
  assert len(files) == 1, 'Found not exactly one file in logdir: %s' % files
  return events_from_file(os.path.join(log_dir, files[0]))


def to_numpy(summary_value):
  """Converts the value of the supplied summary to a numpy array."""
  return tensor_util.MakeNdarray(summary_value.tensor)


def is_summary(event: event_pb2.Event) -> bool:
  """Returns true if the supplied proto event represents a summary that we've
logged, false otherwise."""
  return len(event.summary.value) > 0


def get_summaries(
    events: Iterable[event_pb2.Event]) -> Iterable[Dict[str, Any]]:
  """Returns a sequence of dictionaries represen"""

  def process(e):
    v = e.summary.value[0]
    return {"step": e.step, "k": v.tag, "v": to_numpy(v)}

  return [process(e) for e in events if is_summary(e)]


def test_tensorboard_reporter(tmpdir):
  dir_name = str(tmpdir)

  # report all events.
  with closing(r.TensorboardReporter(dir_name)) as reporter:
    reporter.report_all(0, {"a": 1, "b": 10})
    reporter.report_all(1, {"a": 2, "b": 10, "c": 3})
    reporter.report_all(2, {"a": 3, "b": 11})
    reporter.report(3, "a", 8)
    reporter.report(3, "b", 2)
    reporter.report(6, "b", 10)

  # get all the reported events back out:
  events = events_from_logdir(dir_name)
  ms = get_summaries(events)

  # check that all events were written.
  assert len(ms) == 10

  # check all of the A values:
  assert list(filter(lambda m: m["k"] == "a", ms)) == [{
      "step": 0,
      "k": "a",
      "v": 1
  }, {
      "step": 1,
      "k": "a",
      "v": 2
  }, {
      "step": 2,
      "k": "a",
      "v": 3
  }, {
      "step": 3,
      "k": "a",
      "v": 8
  }]

  # Check all of the b values:
  assert list(filter(lambda m: m["k"] == "b", ms)) == [{
      "step": 0,
      "k": "b",
      "v": 10
  }, {
      "step": 1,
      "k": "b",
      "v": 10
  }, {
      "step": 2,
      "k": "b",
      "v": 11
  }, {
      "step": 3,
      "k": "b",
      "v": 2
  }, {
      "step": 6,
      "k": "b",
      "v": 10
  }]

  # specifically check the C value:
  assert list(filter(lambda m: m["k"] == "c", ms)) == [{
      "step": 1,
      "k": "c",
      "v": 3
  }]
