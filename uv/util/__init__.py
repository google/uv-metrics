"""Utilities grab bag."""

import datetime
import json
from functools import singledispatch
from typing import Any, List

import numpy as np
import tqdm


def to_metric(v: Any) -> float:
  """Converts the incoming item into something we can log.

  TODO convert this to a to_serializable instance if tensorflow is present.

  """
  if hasattr(v, 'numpy'):
    return v.numpy()

  return v


@singledispatch
def to_serializable(val):
  """Used by default."""
  return str(val)


@to_serializable.register(np.float32)
def ts_float32(val):
  """Used if *val* is an instance of numpy.float32."""
  return np.float64(val)


def json_str(item: Any) -> str:
  """Converts the supplied python object to a Python dictionary.

  The difference from json.dumps is that this method makes a best effort to
  serialize anything it finds within a nested structure. np.float32 instances,
  for example.

  """
  return json.dumps(item, default=to_serializable)


def uuid():  # pragma: no cover
  """Generates a sane UUID for use in test files and metric directories."""
  return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def wrap(item: Any) -> List[Any]:
  """Ensures that the input is either a list, or wrapped in a list. Returns []
  for None.

  """
  if item is None:
    return []

  if isinstance(item, list):
    return item

  return [item]


def is_number(s):
  """Returns true if the supplied item can be converted into a float; false
  otherwise.

  """
  try:
    float(s)
    return True
  except ValueError:
    return False


class TqdmFile():
  """Dummy file-like that will write to tqdm's 'write' method, which will in turn
  write back into the supplied file. Use this when you need to redirect some
  stream in such a way that won't cause the tqdm progress bar to reset.

  """
  file = None

  def __init__(self, file):
    self.file = file

  def write(self, x):
    if len(x.rstrip()) > 0:
      tqdm.tqdm.write(x, file=self.file, nolock=False)

  def flush(self):
    return getattr(self.file, "flush", lambda: None)()

  def isatty(self):
    return getattr(self.file, "isatty", lambda: False)()
