#!/usr/bin/python3

import unittest

import test_metadata_updater
import test_metadata_updater_integration


# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(test_metadata_updater))
suite.addTests(loader.loadTestsFromModule(test_metadata_updater_integration))


# initialize a runner, pass it the suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)
