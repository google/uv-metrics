import unittest
import uv.basic as b


class BasicTestSuite(unittest.TestCase):
  """Basic test cases."""

  def test_absolute_truth_and_meaning(self):
    assert True

  def test_cake_squared(self):
    assert b.cake_squared(10) == 100


if __name__ == '__main__':
  unittest.main()
