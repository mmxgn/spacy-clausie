import unittest
from . import claucy_test

def test_suite():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(claucy_test)
    return suite