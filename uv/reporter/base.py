"""Base and Combinators; these classes and functions allow you to compose
reporters together into compound reporters.

"""
from __future__ import annotations

from abc import ABCMeta
from typing import Any, Callable, Dict, Optional, Union

import uv.reader.base as rb
import uv.types as t
import uv.util.prefix as p


class AbstractReporter(metaclass=ABCMeta):
  """Base class for all reporters. A reporter is a type that is able to log
  timeseries of values for different t.MetricKey instances, one item at a time.

  NOTE - by default, report_all and report are implemented in terms of one
  another. This means that you can choose which method you'd like to override,
  or override both... but if you don't override any you'll see infinite
  recursion.

  Be careful not to abuse the kindness!

  """

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

  def plus(self, *others: t.AbstractReporter):
    """Returns an instance of MultiReporter wrapping the current instance. This
    reporter broadcasts its inputs to this instance, plus any other reporters
    supplied to this method, every time it sees a metric passed in via report
    or report_all.

    """
    return MultiReporter(self, *others)

  def filter_step(self,
                  pred: Callable[[int], bool],
                  on_false: Optional[AbstractReporter] = None):
    """Accepts a predicate function from step to boolean, and returns a reporter
    that tests every step against the supplied function. If the function
    returns true, metrics get passed on to this reporter; else, they get
    filtered out.

    If a reporter is supplied to on_false, any time the predicate returns false
    items are routes to that store instead of base.

    """
    return FilterReporter(self, pred, on_false_reporter=on_false)

  def mapv(self, fn: Callable[[t.Metric], t.Metric]):
    """"Accepts a function that acts on metrics seen via report and report_all
    before passing the result of the fn down to this reporter instance.

    """
    return self.map_stepv(lambda _, v: fn(v))

  def map_stepv(self, fn: Callable[[int, t.Metric], t.Metric]):
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


class FilterReporter(AbstractReporter):
  """Reporter that uses a supplied predicate on incoming steps to choose whether
  or not to pass metrics on to an underlying store.

  The reader always queries the base store, not the on_false_reporter.

  Args:
    base: Backing reporter. All report and report_all calls proxy here.
    predicate: function from step to bool. If true, passes on metrics. If
    false, swallows them.
    on_false_reporter: if supplied, this reporter receives items for which the
    predicate returns false.

  """

  def __init__(self,
               base: AbstractReporter,
               predicate: Callable[[int], bool],
               on_false_reporter: Optional[AbstractReporter] = None):
    self._base = base
    self._pred = predicate
    self._on_false_reporter = on_false_reporter

  def report_all(self, step: int, m: Dict[str, Any]) -> None:
    if self._pred(step):
      self._base.report_all(step, m)

    elif self._on_false_reporter:
      self._on_false_reporter.report_all(step, m)

  def report(self, step: int, k: str, v: Any) -> None:
    if self._pred(step):
      self._base.report(step, k, v)

    elif self._on_false_reporter:
      self._on_false_reporter.report(step, k, v)

  def reader(self) -> Optional[rb.AbstractReader]:
    return self._base.reader()

  def close(self) -> None:
    self._base.close()


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

  def report_all(self, step: int, m: Dict[str, Any]) -> None:
    self._base.report_all(step, {k: self._fn(step, v) for k, v in m.items()})

  def report(self, step: int, k: str, v: Any) -> None:
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

  def report_all(self, step: int, m: Dict[str, Any]) -> None:
    for r in self._reporters:
      r.report_all(step, m)

  def report(self, step: int, k: str, v: Any) -> None:
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

  def report_all(self, step: int, m: Dict[str, Any]) -> None:
    self._base.report_all(step, p.attach(m, self._prefix))

  def report(self, step: int, k: str, v: Any) -> None:
    newk = p.attach_s(k, self._prefix)
    self._base.report(step, newk, v)

  def reader(self) -> Optional[rb.AbstractReader]:
    return rb.PrefixedReader(self._base.reader(), self._prefix)

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

  def report_all(self, step: int, m: Dict[str, Any]) -> None:
    self._base.report_all(step, m)

  def report(self, step: int, k: str, v: Any) -> None:
    self._base.report(step, k, v)

  def reader(self) -> Optional[rb.AbstractReader]:
    return self._base.reader()

  def close(self) -> None:
    self._base.close()
