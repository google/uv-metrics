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

import uv.reporter.state as s
import uv.reporter.store as r


def test_global_reporter():
  r1 = r.MemoryReporter()
  reader1 = r1.reader()

  r2 = r.MemoryReporter()
  reader2 = r2.reader()

  r3 = r.MemoryReporter()
  reader3 = r3.reader()

  # By default, we get the null reporter and nothing happens.
  assert s.report(1, "face", 2) is None
  assert s.report_all(2, {"face": 2, "cake": 3}) is None

  s.set_reporter(r1)

  # boom!
  assert s.get_reporter() == r1

  # Now, reports go into the global reporter.
  s.report(1, "face", 2)
  s.report_all(2, {"face": 2, "cake": 3})

  # confirm:
  assert reader1.read("face") == [2, 2]
  assert reader1.read_all(["face", "cake"]) == {"face": [2, 2], "cake": [3]}

  # params are correctly reported.
  s.report_param("key_for_me", "value")
  s.report_params({"k": "v", "k2": "v2"})
  assert r1._params == {"key_for_me": "value", "k": "v", "k2": "v2"}

  with s.active_reporter(r2):

    # params get reported to the proper reporter.
    s.report_param("key", "value")
    assert r1._params == {"key_for_me": "value", "k": "v", "k2": "v2"}
    assert r2._params == {"key": "value"}

    # These report go through to r2, not r1.
    s.report(1, "hammer", 2)
    s.report_all(1, {"steve": 2, "john": 3})

    assert reader1.read_all(["hammer", "steve", "john"]) == {
        "hammer": [],
        "john": [],
        "steve": []
    }

    assert reader2.read_all(["hammer", "steve", "john"]) == {
        "hammer": [2],
        "john": [3],
        "steve": [2]
    }

    # these can nest:
    with s.active_reporter(r3):
      s.report(4, "deeper", 10)

      assert reader2.read("deeper") == []
      assert reader3.read("deeper") == [10]

    # when you leave a block, you hit the next reporter back.
    s.report(4, "deeper", 12)
    assert reader2.read("deeper") == [12]
    assert reader3.read("deeper") == [10]
