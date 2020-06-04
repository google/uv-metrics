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
"""Code for manipulating and joining prefixes and suffixes to metric keys.

TODO convert attach into a single dispatch method, and make a new suffix
method.

"""

from collections import ChainMap
from typing import Dict, Iterable

import uv.types as t
import uv.util as u


def attach_s(s: t.MetricKey,
             a: t.Attachment,
             prefix: bool = True) -> t.MetricKey:
  """Attach the supplied prefix or suffix to the string s."""
  if not isinstance(s, str):
    s = str(s)

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
