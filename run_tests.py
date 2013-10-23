import unittest

import tests.verifyUrlEncode

suite = unittest.TestLoader()
suite = suite.loadTestsFromModule(tests.verifyUrlEncode)

if __name__ == "__main__":
  unittest.TextTestRunner().run(suite)
