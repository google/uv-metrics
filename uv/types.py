"""Types shared between readers and reporters."""

from typing import Any, Dict, Iterable, List, Tuple, Union

# Currently a metric can only be keyed by a string. Prefixes can't act as
# dictionary keys as they're not hashable. We could consider opening this up to
# tuples as well.
MetricKey = str
Metric = Any

Prefix = Union[MetricKey, List[str]]
Suffix = Union[MetricKey, List[str]]
Attachment = Union[Prefix, Suffix]
