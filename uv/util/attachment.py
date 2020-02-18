"""Code for manipulating and joining prefixes and suffixes to metric keys.

TODO convert attach into a single dispatch method, and make a new suffix
method.

"""

from collections import ChainMap
from typing import Any, Dict, Iterable, Union

import uv.types as t
import uv.util as u


def attach_s(s: t.MetricKey,
             a: t.Attachment,
             prefix: bool = True) -> t.MetricKey:
  """Attach the supplied prefix or suffix to the string s."""
  if prefix:
    attached = u.wrap(a) + [s]
  else:
    attached = [s] + u.wrap(a)

  return ".".join(attached)


def attach_iter(xs: Iterable[t.MetricKey],
                a: t.Attachment,
                prefix: bool = True) -> Iterable[t.MetricKey]:
  """Attaches the supplied prefix or suffix to every item in the iterable."""
  return (attach_s(x, a, prefix) for x in xs)


def attach(m: Dict[t.MetricKey, t.Metric],
           a: t.Attachment,
           prefix: bool = True) -> Dict[t.MetricKey, t.Metric]:
  """Attaches the supplied prefix or suffix to every key in the dictionary."""
  return {attach_s(k, a, prefix): v for k, v in m.items()}


def _by_attachment(ms: Dict[str, Dict[t.MetricKey, t.Metric]],
                   prefix: bool = True) -> Dict[t.MetricKey, t.Metric]:
  """Collapse the prefixes into the key. If you do this, you can avoid using
  prefixed reporters.

  """
  return dict(ChainMap(*(attach(m, a, prefix) for a, m in ms.items())))


def by_prefix(
    ms: Dict[t.Attachment, Dict[t.MetricKey, t.Metric]]
) -> Dict[t.MetricKey, t.Metric]:
  """Collapse the prefixes into the key. If you do this, you can avoid using
  prefixed reporters.

  """
  return _by_attachment(ms, prefix=True)


def by_suffix(
    ms: Dict[t.Attachment, Dict[t.MetricKey, t.Metric]]
) -> Dict[t.MetricKey, t.Metric]:
  """Collapse the suffixes into the key. If you do this, you can avoid using
  suffixed reporters.

  """
  return _by_attachment(ms, prefix=False)
