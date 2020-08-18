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
"""Utilities for MLFlow reporter"""

import collections
from typing import Dict, Union, List, Any


def flatten(d: Dict[str, Union[str, Dict]],
            parent_key: str = '',
            sep: str = ':') -> Dict[str, str]:
  """Recursively flattens a nested dictionary into a dictionary
  whose values are not mappings, i.e., a flat dictionary"""

  items: List[Any] = []

  for k, v in d.items():
    new_key = parent_key + sep + k if parent_key else k
    if isinstance(v, collections.MutableMapping):
      items.extend(flatten(v, new_key, sep=sep).items())
    else:
      items.append((new_key, v))

  return dict(items)
