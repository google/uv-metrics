"""Reporter implementation that relies on the PyFilesystem2 abstraction for
filesystems. See https://github.com/PyFilesystem/pyfilesystem2 for more
information on the library.

"""

from typing import Dict, Union

from fs.base import FS

import uv.fs.util as u
import uv.reader.base as rb
import uv.types as t
from uv.fs.reader import FSReader
from uv.reporter.base import AbstractReporter


class FSReporter(AbstractReporter):
  """AbstractReporter implementation backed by an instance of pyfilesystem2's FS
  abstraction. See https://docs.pyfilesystem.org/en/latest/ for more
  information.

  FSReporter serializes each metric as JSON

  TODO add a pluggable serializer, with a default jsonl implementation.

  Args:
    fs: Either an fs URI string, or an actual fs.base.FS object.

  """

  def __init__(self, fs: Union[FS, str]):
    self._fs = u.load_fs(fs)
    self._cache = u.HandleCache(self._fs)

  def _handle(self, k: t.MetricKey):
    """Returns an open handle that points to the file containing the metrics for
    k.

    """
    json_path = u.jsonl_path(k)
    return self._cache.open(json_path, mode='wb')

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    for k, v in m.items():
      handle = self._handle(k)
      contents = u.jsonl_bytes(v)
      handle.write(contents)
      handle.flush()

  def reader(self) -> rb.AbstractReader:
    return FSReader(self._fs)

  def close(self) -> None:
    self._cache.close()
    self._fs.close()
