"""Utilities shared by functions that interact with pyfilesystem2."""

from typing import Any, Union

import fs as pyfs
import uv.types as t
import uv.util as u
from fs.base import FS


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
