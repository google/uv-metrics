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
"""Base and Combinators; these classes and functions allow you to compose
reporters together into compound reporters.

"""
from abc import ABCMeta
from typing import Any, Callable, Dict, Optional

import uv.reader.base as rb
import uv.types as t
import uv.util.attachment as a


class AbstractReporter(metaclass=ABCMeta):
  """Base class for all reporters. A reporter is a type that is able to log
  timeseries of values for different t.MetricKey instances, one item at a time.

  NOTE - by default, report_all and report are implemented in terms of one
  another. This means that you can choose which method you'd like to override,
  or override both... but if you don't override any you'll see infinite
  recursion.

  Be careful not to abuse the kindness!

  """

  def report_param(self, k: str, v: str) -> None:
    """Accepts a key and value parameter and logs these as parameters alongside the
    reported metrics.

    """
    return None

  def report_params(self, m: Dict[str, str]) -> None:
    """Accepts a dict of parameter name -> value, and logs these as parameters
    alongside the reported metrics.

    """
    return None

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    """Accepts a step (an ordered int referencing some timestep) and a dictionary
    of metric key => metric value, and persists the metric into some underlying
    store.

    Extending classes are expected to perform some side effect that's either
    visually useful, as in a live-plot, or recoverable via some matching
    extension of AbstractReader.

    """

    for k, v in m.items():
      self.report(step, k, v)

  def report(self, step: int, k: t.MetricKey, v: t.Metric) -> None:
    """Accepts a step (an ordered int referencing some timestep), a metric key and
    a value, and persists the metric into some underlying store.

    """
    return self.report_all(step, {k: v})

  def reader(self) -> Optional[rb.AbstractReader]:
    """Returns an implementation of AbstractReader that can access the data in this
    store.

    Returns None by default; extending classes are encouraged, but not
    required, to override.

    """
    return None

  def close(self) -> None:
    """Release any resources held open by this reporter instance."""
    return None

  # Combinators.

  def with_prefix(self, prefix: t.Prefix):
    """Returns an instance of PrefixedReporter wrapping the current instance. This
    reporter attaches the supplied prefix to every metric key it sees before
    passing metrics on.

    """
    return PrefixedReporter(self, prefix)

  def with_suffix(self, suffix: t.Suffix):
    """Returns an instance of SuffixedReporter wrapping the current instance. This
    reporter attaches the supplied suffix to every metric key it sees before
    passing metrics on.

    """
    return SuffixedReporter(self, suffix)

  def plus(self, *others: "AbstractReporter"):
    """Returns an instance of MultiReporter wrapping the current instance. This
    reporter broadcasts its inputs to this instance, plus any other reporters
    supplied to this method, every time it sees a metric passed in via report
    or report_all.

    """
    return MultiReporter(self, *others)

  def filter_step(self,
                  pred: Callable[[int], bool],
                  on_false: Optional["AbstractReporter"] = None):
    """Accepts a predicate function from step to boolean, and returns a reporter
    that tests every step against the supplied function. If the function
    returns true, metrics get passed on to this reporter; else, they get
    filtered out.

    If a reporter is supplied to on_false, any time the predicate returns false
    items are routes to that store instead of base.

    """

    def step_pred(step, _):
      return pred(step)

    return FilterValuesReporter(self, step_pred, on_false_reporter=on_false)

  def filter_values(self,
                    pred: Callable[[int, t.Metric], bool],
                    on_false: Optional["AbstractReporter"] = None):
    """"Accepts a function from (step, metric) to boolean; every (step, metric)
    pair passed to report and report_all are passed into this function. If the
    predicate returns true, the metric is passed on; else, it's filtered.

    """
    return FilterValuesReporter(self, pred, on_false_reporter=on_false)

  def map_values(self, fn: Callable[[int, t.Metric], t.Metric]):
    """"Accepts a function from (step, metric) to some new metric; every (step,
    metric) pair passed to report and report_all are passed into this function,
    and the result is passed down the chain to this, the calling reporter.

    """
    return MapValuesReporter(self, fn)

  def stepped(self, step_key: Optional[str] = None):
    """Returns a new reporter that modifies incoming metrics by wrapping them in a
    dict of this form before passing them down to this instance of reporter:

    {step_key: step, "value": metric_value}

    where step_key is the supplied argument, and equal to "step" by default.
    This is useful for keeping track of each metric's timestamp.

    """
    return stepped_reporter(self, step_key=step_key)

  def report_each_n(self, n: int):
    """Returns a new reporter that only reports every n steps; specifically, the
    new reporter will only accept metrics where step % n == 0.

    If n <= 1, this reporter, untouched, is returned directly.

    """
    n = max(1, n)
    if n > 1:
      return self.filter_step(lambda step: step % n == 0)
    else:
      return self

  def from_thunk(self, thunk: Callable[[], Dict[t.MetricKey, t.Metric]]):
    """Returns a new Reporter that passes all AbstractReporter methods through, but
    adds a new method called "thunk()" that, when called, will pass the emitted
    map of metric key to metric down to the underlying store.

    thunk() returns the value emitted by the no-arg function passed here via
    `thunk`.
    """
    return ThunkReporter(self, thunk)


# Combinators


def stepped_reporter(base: AbstractReporter,
                     step_key: Optional[str] = None) -> AbstractReporter:
  """Returns a new reporter that modifies incoming metric by wrapping them in a
  dict of this form before passing them down to base:

    {step_key: step, "value": metric_value}

  where step_key is the supplied argument, and equal to "step" by default. This
  is useful for keeping track of each metric's timestamp.

  """
  if step_key is None:
    step_key = "step"

  def _augment(step: int, v: Any) -> Dict[str, Any]:
    return {step_key: step, "value": v}

  return MapValuesReporter(base, _augment)


class FilterValuesReporter(AbstractReporter):
  """Reporter that filters incoming metrics by applying a predicate from (step,
  t.Metric). If true, the reporter passes the result on to the underlying
  reporter. Else, nothing.

  Args:
    base: Backing reporter. All report and report_all calls proxy here.
    predicate: function from (step, metric) to metric.

  """

  def __init__(self,
               base: AbstractReporter,
               predicate: Callable[[int, t.Metric], bool],
               on_false_reporter: Optional[AbstractReporter] = None):
    self._base = base
    self._pred = predicate
    self._on_false_reporter = on_false_reporter

  def report_param(self, k: str, v: str) -> None:
    return self._base.report_param(k, v)

  def report_params(self, m: Dict[str, str]) -> None:
    return self._base.report_params(m)

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    good = {k: v for k, v in m.items() if self._pred(step, v)}
    bad = {k: v for k, v in m.items() if not self._pred(step, v)}

    if good:
      self._base.report_all(step, good)

    if self._on_false_reporter and bad:
      self._on_false_reporter.report_all(step, bad)

  def report(self, step: int, k: t.MetricKey, v: t.Metric) -> None:
    if self._pred(step, v):
      self._base.report(step, k, v)

    elif self._on_false_reporter:
      self._on_false_reporter.report(step, k, v)

  def reader(self) -> Optional[rb.AbstractReader]:
    return self._base.reader()

  def close(self) -> None:
    self._base.close()

    if self._on_false_reporter:
      self._on_false_reporter.close()


class MapValuesReporter(AbstractReporter):
  """Reporter that modifies incoming metrics by applying a function from (step,
  t.Metric) to a new metric before passing the result on to the underlying
  reporter.

  Args:
    base: Backing reporter. All report and report_all calls proxy here.
    fn: function from (step, metric) to metric.

  """

  def __init__(self, base: AbstractReporter, fn: Callable[[int, t.Metric],
                                                          t.Metric]):
    self._base = base
    self._fn = fn

  def report_param(self, k: str, v: str) -> None:
    return self._base.report_param(k, v)

  def report_params(self, m: Dict[str, str]) -> None:
    return self._base.report_params(m)

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    self._base.report_all(step, {k: self._fn(step, v) for k, v in m.items()})

  def report(self, step: int, k: t.MetricKey, v: t.Metric) -> None:
    self._base.report(step, k, self._fn(step, v))

  def reader(self) -> Optional[rb.AbstractReader]:
    return self._base.reader()

  def close(self) -> None:
    self._base.close()


class MultiReporter(AbstractReporter):
  """Reporter that broadcasts out metrics to all N reporters supplied to its
  constructor.

  Args:
    reporters: instances of t.AbstractReporter that will receive all calls to
               this instance's methods.

  """

  def __init__(self, *reporters: AbstractReporter):
    self._reporters = reporters

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    for r in self._reporters:
      r.report_all(step, m)

  def report(self, step: int, k: t.MetricKey, v: t.Metric) -> None:
    for r in self._reporters:
      r.report(step, k, v)

  def close(self) -> None:
    for r in self._reporters:
      r.close()


class PrefixedReporter(AbstractReporter):
  """Reporter that prepends a prefix to all keys before passing requests on to
  the supplied backing reporter.

  Args:
    base: Backing reporter. All report and report_all calls proxy here.
    prefix: the prefix to attach to all keys supplied to any method.

  """

  def __init__(self, base: AbstractReporter, prefix: t.Prefix):
    self._base = base
    self._prefix = prefix

  def report_param(self, k: str, v: str) -> None:
    return self._base.report_param(k, v)

  def report_params(self, m: Dict[str, str]) -> None:
    return self._base.report_params(m)

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    self._base.report_all(step, a.attach(m, self._prefix, prefix=True))

  def report(self, step: int, k: t.MetricKey, v: t.Metric) -> None:
    newk = a.attach_s(k, self._prefix, prefix=True)
    self._base.report(step, newk, v)

  def reader(self) -> Optional[rb.AbstractReader]:
    return rb.PrefixedReader(self._base.reader(), self._prefix)

  def close(self) -> None:
    self._base.close()


class SuffixedReporter(AbstractReporter):
  """Reporter that prepends a prefix to all keys before passing requests on to
  the supplied backing reporter.

  Args:
    base: Backing reporter. All report and report_all calls proxy here.
    suffix: the suffix to attach to all keys supplied to any method.

  """

  def __init__(self, base: AbstractReporter, suffix: t.Suffix):
    self._base = base
    self._suffix = suffix

  def report_param(self, k: str, v: str) -> None:
    return self._base.report_param(k, v)

  def report_params(self, m: Dict[str, str]) -> None:
    return self._base.report_params(m)

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    self._base.report_all(step, a.attach(m, self._suffix, prefix=False))

  def report(self, step: int, k: t.MetricKey, v: t.Metric) -> None:
    newk = a.attach_s(k, self._suffix, prefix=False)
    self._base.report(step, newk, v)

  def reader(self) -> Optional[rb.AbstractReader]:
    return rb.SuffixedReader(self._base.reader(), self._suffix)

  def close(self) -> None:
    self._base.close()


class ThunkReporter(AbstractReporter):
  """Reporter that passes all AbstractReporter methods through, but adds a new
  method called "thunk()" that, when called, will pass the emitted map of
  metric key to metric down to the underlying store.

  Args:
    base: Backing reporter. All report and report_all calls proxy here.
    thunk: no-arg lambda that returns a metric dictionary.

  """

  def __init__(self, base: AbstractReporter, thunk):
    self._base = base
    self._thunk = thunk

  def thunk(self, step: int) -> None:
    self.report_all(step, self._thunk())

  def report_param(self, k: str, v: str) -> None:
    return self._base.report_param(k, v)

  def report_params(self, m: Dict[str, str]) -> None:
    return self._base.report_params(m)

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    self._base.report_all(step, m)

  def report(self, step: int, k: t.MetricKey, v: t.Metric) -> None:
    self._base.report(step, k, v)

  def reader(self) -> Optional[rb.AbstractReader]:
    return self._base.reader()

  def close(self) -> None:
    self._base.close()
