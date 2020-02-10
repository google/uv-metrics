"""The base AbstractReader class, along with all of the subclasses that
AbstractReader is able to return from any of its methods."""

from abc import ABCMeta
from typing import Dict, List, Union

import uv.types as t
import uv.util.prefix as p


class AbstractReader(metaclass=ABCMeta):
  """Base class for all classes that are able to track and return lists of
  metrics, keyed by a supplied t.MetricKey.

  NOTE - by default, read_all and read are implemented in terms of one another.
  This means that you can choose which method you'd like to override, or
  override both... but if you don't override any you'll see infinite recursion.

  Be careful not to abuse the kindness!

  """

  def read_all(self,
               ks: List[t.MetricKey]) -> Dict[t.MetricKey, List[t.Metric]]:
    """Accepts a list of t.MetricKey instances and returns a mapping of t.MetricKey
    to a list of all metrics ever logged using that MetricKey.

    The interface requires that the set of keys in the returned dictionary
    equal the input set; any missing key in the store has to map to a default
    empty list.

    """
    return {k: self.read(k) for k in ks}

  def read(self, k: t.MetricKey) -> List[t.Metric]:
    """Returns a list of all metrics ever logged for the supplied t.MetricKey, or
    an empty list if the backing store has no record.

    """
    return self.read_all([k])[k]

  def close(self) -> None:
    """Release any resources held open by this reader instance."""
    return None

  # Combinators

  def with_prefix(self, prefix: t.Prefix):
    """"Returns a new reader that will pass through all methods to this reader
    instance; the only difference will be that every t.MetricKey instance
    supplied to read or read_all will have the supplied prefix attached.

    """
    return PrefixedReader(self, prefix)


class PrefixedReader(AbstractReader):
  """Reader that prepends a prefix to all keys before passing requests on to the
  supplied backing store.

  Args:
    base: Backing reader. All read and read_all calls proxy here.
    prefix: the prefix to attach to all keys supplied to any method.

  """

  def __init__(self, base: AbstractReader, prefix: t.Prefix):
    self._base = base
    self._prefix = prefix

  def read_all(self,
               ks: List[t.MetricKey]) -> Dict[t.MetricKey, List[t.Metric]]:
    return self._base.read_all(p.attach_iter(ks, self._prefix))

  def read(self, k: t.MetricKey) -> List[t.Metric]:
    return self._base.read(p.attach_s(k, self._prefix))

  def close(self) -> None:
    self._base.close()
