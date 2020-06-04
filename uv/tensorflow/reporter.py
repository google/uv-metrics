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
"""Tensorflow / Tensorboard reporter that conforms to UV's reporter interface.

In its current form, the TensorboardReporter is able to report scalars.

TODO Add support for logging images directly using:
https://github.com/tensorflow/tensorflow/blob/r2.1/tensorflow/python/keras/callbacks.py#L1400

TODO investigate docs on how to serialize entries:
https://github.com/tensorflow/tensorboard/blob/master/docs/r1/summaries.md

"""

from typing import Dict, Optional

import tensorflow as tf

import uv.reporter.base as b
import uv.types as t


class TensorboardReporter(b.AbstractReporter):
  """Reporter implementation that accepts scalar metrics and reports them to an
  underlying Tensorboard file writer in the supplied directory.

  TensorboardReporter's log_dir argument can be either a local path or a GCloud
  path, prefixed with gs://.

  Arguments to the TensorboardReporter constructor match the arguments of
  https://www.tensorflow.org/api_docs/python/tf/summary/create_file_writer.



  Args:
    log_dir: a string specifying the directory in which to write an event file.
    max_queue: the largest number of summaries to keep in a queue; will
     flush once the queue gets bigger than this. Defaults to 100.
    flush_millis: the largest interval between flushes. Defaults to 120,000.
    filename_suffix: optional suffix for the event file name. Defaults to `.v2`.
    name: a name for the op that creates the writer.

  """

  def __init__(
      self,
      log_dir: str,
      max_queue: Optional[int] = 100,
      flush_millis: Optional[int] = None,
      filename_suffix: Optional[str] = None,
  ):
    self._path = log_dir
    self._writer = tf.summary.create_file_writer(
        self._path,
        max_queue=max_queue,
        flush_millis=flush_millis,
        filename_suffix=filename_suffix)

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    with self._writer.as_default():
      for k, v in m.items():
        tf.summary.scalar(k, v, step=step)

    self._writer.flush()

  def report(self, step: int, k: t.MetricKey, v: t.Metric) -> None:
    with self._writer.as_default():
      tf.summary.scalar(k, v, step=step)

  def close(self) -> None:
    self._writer.close()
