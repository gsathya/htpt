import unittest

import tests.verifyUrlEncode
import tests.verifyFrame

suite = unittest.TestLoader()
suite = suite.loadTestsFromModule(tests.verifyUrlEncode)
suite.addTest(unittest.TestLoader().loadTestsFromModule(tests.verifyFrame))

if __name__ == "__main__":
  unittest.TextTestRunner().run(suite)
