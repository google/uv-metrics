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

  test_manager.add_measurement({
      'name': 'L2',
      'interval': 10,
      'function': lambda state: 0
  })

  assert len(test_manager.measurements) == 1
  assert 'L2' in test_manager.measurements.keys()
  assert test_manager.measurements['L2']['interval'] == 10
  assert test_manager.measurements['L2']['function'](static_state) == 0


def test_measurement_invervals():
  """Tests that measurements occur at the specified intervals"""

  data_store = {}
  reporter = r.MemoryReporter(data_store).stepped()
  static_state = {}

  test_manager = m.MeasurementManager(static_state, reporter)

  test_intervals = [10, 13, 17, 20]
  for interval in test_intervals:
    test_manager.add_measurement({
        'name': f'Int_{interval}',
        'interval': interval,
        'function': lambda state: 0
    })

  TEST_STEPS = 100
  for i in range(TEST_STEPS):
    test_manager.process(i, {})

  # check data_store
  assert data_store == {
      'Int_10': [{
          'step': 0,
          'value': 0
      }, {
          'step': 10,
          'value': 0
      }, {
          'step': 20,
          'value': 0
      }, {
          'step': 30,
          'value': 0
      }, {
          'step': 40,
          'value': 0
      }, {
          'step': 50,
          'value': 0
      }, {
          'step': 60,
          'value': 0
      }, {
          'step': 70,
          'value': 0
      }, {
          'step': 80,
          'value': 0
      }, {
          'step': 90,
          'value': 0
      }],
      'Int_13': [{
          'step': 0,
          'value': 0
      }, {
          'step': 13,
          'value': 0
      }, {
          'step': 26,
          'value': 0
      }, {
          'step': 39,
          'value': 0
      }, {
          'step': 52,
          'value': 0
      }, {
          'step': 65,
          'value': 0
      }, {
          'step': 78,
          'value': 0
      }, {
          'step': 91,
          'value': 0
      }],
      'Int_17': [{
          'step': 0,
          'value': 0
      }, {
          'step': 17,
          'value': 0
      }, {
          'step': 34,
          'value': 0
      }, {
          'step': 51,
          'value': 0
      }, {
          'step': 68,
          'value': 0
      }, {
          'step': 85,
          'value': 0
      }],
      'Int_20': [{
          'step': 0,
          'value': 0
      }, {
          'step': 20,
          'value': 0
      }, {
          'step': 40,
          'value': 0
      }, {
          'step': 60,
          'value': 0
      }, {
          'step': 80,
          'value': 0
      }]
  }


def test_state_usage():
  """ Tests that the measurements are made on the proper state,
  i.e. the static and dynamic states are used appropriately """
  data_store = {}
  reporter = r.MemoryReporter(data_store).stepped()
  static_state = {'Value1': 2., 'Value2': 4.}

  test_manager = m.MeasurementManager(static_state, reporter)

  test_manager.add_measurement({
      'name': 'Value1',
      'interval': 3,
      'function': lambda x: x['Value1']
  })
  test_manager.add_measurement({
      'name': 'Value2',
      'interval': 3,
      'function': lambda x: x['Value2']
  })
  test_manager.add_measurement({
      'name': 'sum_12',
      'interval': 3,
      'function': lambda x: x['Value2'] + x['Value1']
  })
  test_manager.add_measurement({
      'name': 'sum_13',
      'interval': 3,
      'function': lambda x: x['Value1'] + x['Value3']
  })
  test_manager.add_measurement({
      'name': 'Value3',
      'interval': 3,
      'function': lambda x: x['Value3']
  })

  TEST_STEPS = 5
  for step in range(TEST_STEPS):
    dynamic_state = {'Value3': step * step}
    test_manager.process(step, dynamic_state)

  assert data_store == {
      'Value1': [{
          'step': 0,
          'value': 2.
      }, {
          'step': 3,
          'value': 2.
      }],
      'Value2': [{
          'step': 0,
          'value': 4.
      }, {
          'step': 3,
          'value': 4.
      }],
      'sum_12': [{
          'step': 0,
          'value': 6.
      }, {
          'step': 3,
          'value': 6.
      }],
      'sum_13': [{
          'step': 0,
          'value': 2.
      }, {
          'step': 3,
          'value': 11.
      }],
      'Value3': [{
          'step': 0,
          'value': 0
      }, {
          'step': 3,
          'value': 9
      }]
  }
