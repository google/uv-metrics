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
"""Tests of metriccallback functions."""

import uv.reporter as r
import uv.experimental.metriccallback as m
import pytest


def test_setup():
  """Tests whether the MetricCallback() object is setup
  without error"""

  static_state = {}

  test_obj = m.MetricCallback(static_state)


def test_add_measurement():
  """Tests that measurements can be added to a MetricCallback
  object properly """

  static_state = {}

  test_obj = m.MetricCallback(static_state)

  assert len(test_obj.measurements) == 0

  INTERVAL = 10
  MEASURED_VALUE = 0
  MEASUREMENT_NAME = 'L2'

  test_obj.add_measurement({
      'name': MEASUREMENT_NAME,
      'trigger': lambda step: step % INTERVAL == 0,
      'function': lambda state: MEASURED_VALUE
  })

  assert len(test_obj.measurements) == 1
  assert MEASUREMENT_NAME in test_obj.measurements.keys()
  for i in range(3):
    assert test_obj.measurements[MEASUREMENT_NAME]['trigger'](i * INTERVAL)
  assert test_obj.measurements[MEASUREMENT_NAME]['function'](
      static_state) == MEASURED_VALUE


def test_measurement_invervals():
  """Tests that measurements occur at the specified intervals"""

  static_state = {}

  data_store = {}
  reporter = r.MemoryReporter(data_store).stepped()
  test_obj = m.MetricCallback(static_state)

  # log the value 0 at these intervals:
  test_intervals = [10, 13, 17, 20]
  MEASURED_VALUE = 0

  def build_trigger_function(n):

    def trigger_function(step):
      return step % n == 0

    return trigger_function

  for interval in test_intervals:
    test_obj.add_measurement({
        'name': f'Int_{interval}',
        'trigger': build_trigger_function(interval),
        'function': lambda state: MEASURED_VALUE
    })

  TEST_STEPS = 100
  for step in range(TEST_STEPS):
    step_measurements = test_obj.measure(step, {})
    if step_measurements is not None:
      reporter.report_all(step, step_measurements)

  # check data_store
  assert data_store == {
      f'Int_{k}': [{
          'step': s,
          'value': MEASURED_VALUE
      } for s in range(0, TEST_STEPS, k)] for k in test_intervals
  }


def test_state_usage():
  """ Tests that the measurements are made on the proper state,
  i.e. the static and dynamic states are used appropriately """
  # parameters of the test
  VALUE1 = 2.
  VALUE2 = 4.
  INTERVAL = 3
  TEST_STEPS = 5

  static_state = {'Value1': VALUE1, 'Value2': VALUE2}

  data_store = {}
  reporter = r.MemoryReporter(data_store).stepped()
  test_obj = m.MetricCallback(static_state)

  test_obj.add_measurement({
      'name': 'Static1',
      'trigger': lambda step: step % INTERVAL == 0,
      'function': lambda x: x['Value1']
  })
  test_obj.add_measurement({
      'name': 'Static2',
      'trigger': lambda step: step % INTERVAL == 0,
      'function': lambda x: x['Value2']
  })
  test_obj.add_measurement({
      'name': 'StaticSum',
      'trigger': lambda step: step % INTERVAL == 0,
      'function': lambda x: x['Value2'] + x['Value1']
  })
  test_obj.add_measurement({
      'name': 'DynamicSum',
      'trigger': lambda step: step % INTERVAL == 0,
      'function': lambda x: x['Value1'] + x['Value3']
  })
  test_obj.add_measurement({
      'name': 'Dynamic3',
      'trigger': lambda step: step % INTERVAL == 0,
      'function': lambda x: x['Value3']
  })

  for step in range(TEST_STEPS):
    dynamic_state = {'Value3': step * step}
    step_measurements = test_obj.measure(step, dynamic_state)
    if step_measurements is not None:
      reporter.report_all(step, step_measurements)

  # build the desired result to check against
  steps_measured = range(0, TEST_STEPS, INTERVAL)

  assert data_store == {
      'Static1': [{
          'step': step,
          'value': VALUE1
      } for step in steps_measured],
      'Static2': [{
          'step': step,
          'value': VALUE2
      } for step in steps_measured],
      'StaticSum': [{
          'step': step,
          'value': VALUE1 + VALUE2
      } for step in steps_measured],
      'DynamicSum': [{
          'step': step,
          'value': VALUE1 + step * step
      } for step in steps_measured],
      'Dynamic3': [{
          'step': step,
          'value': step * step
      } for step in steps_measured]
  }


def test_force_measure():
  """ Tests that the measurement manager handles forced measurements, i.e.
  measurements provided as a measurement_list argument, properly """

  data_store = {}
  reporter = r.MemoryReporter(data_store).stepped()

  STATIC1 = 3.14
  MEASURE_STEP = 4

  static_state = {'STATIC1': STATIC1}
  test_obj = m.MetricCallback(static_state)

  test_obj.add_measurement({
      'name': "STATIC",
      'trigger': lambda x: False,
      'function': lambda x: x['STATIC1']
  })
  test_obj.add_measurement({
      'name': "NOTMEASURED",
      'trigger': lambda x: False,
      'function': lambda x: 10.
  })

  step_measurements = test_obj.measure(MEASURE_STEP, {}, ['STATIC'])
  if step_measurements is not None:
    reporter.report_all(MEASURE_STEP, step_measurements)

  assert data_store == {'STATIC': [{'step': MEASURE_STEP, 'value': STATIC1}]}
