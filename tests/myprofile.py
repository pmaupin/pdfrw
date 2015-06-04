import cProfile
import unittest
import test_roundtrip

cProfile.run('unittest.main(test_roundtrip)')
