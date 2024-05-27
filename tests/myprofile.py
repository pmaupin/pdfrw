import cProfile
import unittest
from . import test_roundtrip

cProfile.run('unittest.main(test_roundtrip)')
