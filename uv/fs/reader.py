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
"""Reader implementation that relies on the PyFilesystem2 abstraction for
filesystems. See https://github.com/PyFilesystem/pyfilesystem2 for more
information on the library.

"""

import json
from typing import Iterable, List, Union

import fs as pyfs
import uv.fs.util as u
import uv.types as t
from casfs.base import CASFS, Key
from fs.base import FS
from fs.zipfs import ZipFS
from uv.reader.base import AbstractReader, IterableReader


class FSReader(AbstractReader, IterableReader):
  """AbstractReader implementation backed by an instance of pyfilesystem2's FS
  abstraction.

  Args:
    fs: Either an fs URI string, or an actual fs.base.FS object.

  """

  def __init__(self, fs: Union[FS, str]):
    self._fs = u.load_fs(fs)

  def keys(self) -> Iterable[t.Metric]:
    """Returns all files in the filesystem that plausibly contains metrics in jsonl
    format.

    """
    for p in self._fs.walk.files(filter=['*.jsonl']):
      base = pyfs.path.basename(p)
      k, _ = pyfs.path.splitext(base)
      yield k

  def read(self, k: t.MetricKey) -> List[t.Metric]:
    try:
      abs_path = u.jsonl_path(k)
      with self._fs.open(abs_path, mode='rb') as handle:
        lines = handle.read().splitlines()
        return [json.loads(s.decode("utf-8")) for s in lines]

    except pyfs.errors.ResourceNotFound:
      return []

  def close(self) -> None:
    self._fs.close()


class CASReader(FSReader):
  """Override that closes the file too."""

  def __init__(self, cas: CASFS, k: Key):
    self._handle = cas.open(k)
    zfs = ZipFS(self._handle)

    super(CASReader, self).__init__(zfs)

  def close(self) -> None:
    super(CASReader, self).close()
    self._handle.close()
