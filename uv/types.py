"""Types shared between readers and reporters."""

from typing import Any, Dict, Iterable, List, Tuple, Union

# Currently a metric can only be keyed by a string. Prefixes can't act as
# dictionary keys as they're not hashable. We could consider opening this up to
# tuples as well.
MetricKey = str
Metric = Any

Prefix = Union[MetricKey, List[str]]
MetricMap = Dict[MetricKey, Metric]
PrefixDict = Dict[MetricKey, MetricMap]
PrefixIter = Iterable[Tuple[Prefix, MetricMap]]

# iterable of prefixes paired with a metric key. Helps with readers.
PrefixPairs = Iterable[Tuple[Prefix, MetricKey]]

# dictionary of prefix string to a metric key.
PrefixToKey = Dict[str, MetricKey]
