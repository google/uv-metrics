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
"""Utilities shared by functions that interact with pyfilesystem2."""

import io
from typing import Any, Union

import fs as pyfs
import uv.types as t
import uv.util as u
from casfs import CASFS
from fs.base import FS
from fs.copy import copy_fs
from fs.zipfs import ZipFS


class HandleCache():
  """Class that opens file-handles and maintains an internal cache of those
  handles. On close, closes the supplied filesystem, closes all handles and
  clears the cache.

  """

  def __init__(self, fs: FS):
    self._m = {}
    self._fs = fs

  def open(self, path: str, mode: str):
    abs_path = pyfs.path.abspath(path)
    handle = self._m.get(abs_path)

    if handle is None:
      handle = self._fs.open(abs_path, mode=mode)
      self._m[abs_path] = handle

    return handle

  def clear(self) -> None:
    for _, handle in self._m.items():
      handle.close()

    self._m.clear()

  def close(self) -> None:
    self.clear()
    self._fs.close()


def load_fs(root: Union[FS, str]) -> FS:
  """If str is supplied, returns an instance of OSFS, backed by the local
    filesystem; else, returns the filesystem argument directly. Errors if
    supplied with an invalid argument.

    """
  if isinstance(root, str):
    return pyfs.open_fs(root, create=True)

  if isinstance(root, FS):
    return root

  raise ValueError("Not a filesystem or path!")


def jsonl_path(k: t.MetricKey) -> str:
  """Returns an absolute path with an appropriate suffix for a jsonl file."""
  return pyfs.path.abspath("{}.jsonl".format(k))


def to_bytes(item: Union[str, bytes]) -> bytes:
  """Accepts either a bytes instance or a string; if str, returns a bytes
  instance, else acts as identity.

  """
  ret = item

  if not isinstance(item, bytes):
    ret = bytes(item, "utf8")

  return ret


def jsonl_bytes(v: Any) -> bytes:
  """Returns a bytes instance containing a single line of json with a newline
  appended.

  """
  return to_bytes(u.json_str(v) + "\n")


def get_cas(cas_input):
  """Version of the CASFS constructor that creates directories that don't exist.
  TODO delete this once we get that idea merged back into CASFS.

  """
  cas_fs = pyfs.open_fs(cas_input, create=True)
  return CASFS(cas_fs)


def persist_to_cas_via_memory(cfs, source_fs):
  """Example call:

  persist_to_cas_via_memory(
    CASFS("/Users/samritchie/casfs"),
    "/Users/samritchie/tester" # metrics directory
  )

  """
  with io.BytesIO() as f:
    # make sure the ZipFS closes before we attempt to transfer its contents
    # over to the content addressable store.
    with ZipFS(f, write=True) as zfs:
      copy_fs(source_fs, zfs)

    return cfs.put(f)
