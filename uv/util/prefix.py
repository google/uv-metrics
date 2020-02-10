"""Code for manipulating and joining prefixes to metric keys.

TODO convert attach into a single dispatch method, and make a new suffix
method.

"""

from collections import ChainMap
from typing import Any, Dict, Iterable

import uv.types as t
import uv.util as u


def attach_s(s: str, prefix: t.Prefix) -> str:
  """get them all formatted properly into something we can toss over the wire.

  """
  return ".".join(u.wrap(prefix) + [s])


def attach_iter(xs: Iterable[str], prefix: t.Prefix) -> Iterable[str]:
  """Attaches the supplied prefix to every key in the dictionary."""
  return (attach_s(x, prefix) for x in xs)


def attach(m: Dict[str, Any], prefix: t.Prefix) -> Dict[str, Any]:
  """Attaches the supplied prefix to every key in the dictionary."""
  return {attach_s(k, prefix): v for k, v in m.items()}


def by_prefix(ms: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
  """Collapse the prefixes into the key. If you do this, you can avoid using
  prefixed reporters.

  """
  return dict(ChainMap(*(attach(m, p) for p, m in ms.items())))
