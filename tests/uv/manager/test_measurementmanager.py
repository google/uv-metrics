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
"""Tests of manager functions."""

import uv.reporter as r
import uv.manager as m
import pytest


def test_manager_setup():
  """Tests whether the MeasurementManager() object is setup
  without error"""

  reporter = r.MemoryReporter().stepped()
  static_state = {}

  test_manager = m.MeasurementManager(static_state, reporter)


def test_add_measurement():
  """Tests that measurements can be added to a MeasurementManager
  object properly """

  reporter = r.MemoryReporter().stepped()
  static_state = {}

  test_manager = m.MeasurementManager(static_state, reporter)

  assert len(test_manager.measurements) == 0

  INTERVAL = 10
  MEASURED_VALUE = 0
  MEASUREMENT_NAME = 'L2'

  test_manager.add_measurement({
      'name': MEASUREMENT_NAME,
      'interval': INTERVAL,
      'function': lambda state: MEASURED_VALUE
  })

  assert len(test_manager.measurements) == 1
  assert MEASUREMENT_NAME in test_manager.measurements.keys()
  assert test_manager.measurements[MEASUREMENT_NAME]['interval'] == INTERVAL
  assert test_manager.measurements[MEASUREMENT_NAME]['function'](
      static_state) == MEASURED_VALUE

  # Test that adding a measurement with interval less-than or equal to
  # zero reaises an exception
  TEST_INTERVALS = [-10, 0]
  for test_interval in TEST_INTERVALS:
    with pytest.raises(Exception):
      assert test_manager.add_measurement({
          'name': MEASUREMENT_NAME,
          'interval': test_interval,
          'function': lambda state: MEASURED_VALUE
      })


def test_measurement_invervals():
  """Tests that measurements occur at the specified intervals"""

  data_store = {}
  reporter = r.MemoryReporter(data_store).stepped()
  static_state = {}

  test_manager = m.MeasurementManager(static_state, reporter)

  # log the value 0 at these intervals:
  test_intervals = [10, 13, 17, 20]
  MEASURED_VALUE = 0

  for interval in test_intervals:
    test_manager.add_measurement({
        'name': f'Int_{interval}',
        'interval': interval,
        'function': lambda state: MEASURED_VALUE
    })

  TEST_STEPS = 100
  for i in range(TEST_STEPS):
    test_manager.measure(i, {})

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
  data_store = {}
  reporter = r.MemoryReporter(data_store).stepped()

  # parameters of the test
  VALUE1 = 2.
  VALUE2 = 4.
  INTERVAL = 3
  TEST_STEPS = 5

  static_state = {'Value1': VALUE1, 'Value2': VALUE2}

  test_manager = m.MeasurementManager(static_state, reporter)

  test_manager.add_measurement({
      'name': 'Static1',
      'interval': INTERVAL,
      'function': lambda x: x['Value1']
  })
  test_manager.add_measurement({
      'name': 'Static2',
      'interval': INTERVAL,
      'function': lambda x: x['Value2']
  })
  test_manager.add_measurement({
      'name': 'StaticSum',
      'interval': INTERVAL,
      'function': lambda x: x['Value2'] + x['Value1']
  })
  test_manager.add_measurement({
      'name': 'DynamicSum',
      'interval': INTERVAL,
      'function': lambda x: x['Value1'] + x['Value3']
  })
  test_manager.add_measurement({
      'name': 'Dynamic3',
      'interval': INTERVAL,
      'function': lambda x: x['Value3']
  })

  for step in range(TEST_STEPS):
    dynamic_state = {'Value3': step * step}
    test_manager.measure(step, dynamic_state)

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
  test_manager = m.MeasurementManager(static_state, reporter)

  test_manager.add_measurement({
      'name': "STATIC",
      'interval': 3,
      'function': lambda x: x['STATIC1']
  })
  test_manager.add_measurement({
      'name': "NOTMEASURED",
      'interval': 3,
      'function': lambda x: 10.
  })

  test_manager.measure(MEASURE_STEP, {}, ['STATIC'])

  assert data_store == {'STATIC': [{'step': MEASURE_STEP, 'value': STATIC1}]}
