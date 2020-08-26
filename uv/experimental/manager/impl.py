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
"""The MeasurementManager class, which conducts and reports on measurements
which may be measured at varying intervals through training."""

from typing import Dict, Iterable, List, Any, Union, Callable, Optional
from uv.reporter import AbstractReporter


class MeasurementManager:
  """Class for a MeasurementManager.  This manager is instantiated with a
  particular reporter, which it will use to report whatever measurements is
  conducts.

  The MeasurementManager has a set of measurements---stored in a dictionary
  (described below)---which are to be carried out at a certain frequency, which
  is specific to each measurement.

  Whenever the MeasurementManager's process() function is called, with a
  step number provided as an argument, the MeasurementManager decides which
  measurements are required at each step, carries them out, and reports them.

  In order to carry out the measurement, the Manager has a state (Dict) at each
  step, which contains all the information necessary to perform the measurement.
  Part of this state is static (e.g., the training dataset), while part can
  change at each step.  This dynamic state is passed along in the process() call.

  Args:
    static_state: Dict of variables which will be used to compute the measured
                  values.  The static_state is fixed throughout time.
    reporter: Reporter which will report the measurements.
  """

  def __init__(self, static_state: Dict[str, Any], reporter: AbstractReporter):
    self.static_state = static_state
    self.reporter = reporter
    self.measurements = {}

  def add_measurement(self, measurement_spec: Dict[str, Union[str, int,
                                                              Callable]]):
    """Adds a measurement specification to the MeasurementManager.
    Args:
      measurement_spec: Dict containing keys:
        'name': String, the name of the measurement, e.g. 'training_loss'
        'interval': Integer, how often to measure
        'function': Function, taking in the state_dictionary, and returning the
                              measured value
    """
    name = measurement_spec['name']

    if measurement_spec['interval'] <= 0:
      raise ValueError(
          'measurement_spec[\'interval\'] must be greater than zero')

    self.measurements[name] = {
        'interval': measurement_spec['interval'],
        'function': measurement_spec['function']
    }

  def measure(self,
              step: int,
              dynamic_state: Dict[str, Any],
              measurement_list: Optional[Iterable[str]] = None):
    """ At a given step, decide which measurements need to be
    performed at this step and perform them

    Args:
      step: Integer, the number of the current step
      dynamic_state: Dict, the state variables necessary to perform the
                    measurement
      measurement_list: Iterable[str], the list of measurements to make this
                        step.
                        If not provided (more common behavior), report the
                        measurements required by the measurements' intervals.
    """

    # Add measurements required by this step to the specified measurements
    if measurement_list is None:
      measurement_list = self.triggered(step)

    full_state = {**self.static_state, **dynamic_state}

    measurements = {}
    for name in measurement_list:
      measurement_fn = self.measurements[name]['function']
      measured_value = measurement_fn(full_state)

      measurements[name] = measured_value

    if len(measurements) > 0:
      self.reporter.report_all(step, measurements)

  def triggered(self, step: int) -> Iterable[str]:
    """ Returns an iterable of measurement names which are to be
    performed a the given step """

    for name, spec in self.measurements.items():
      if step % spec['interval'] == 0:
        yield name
