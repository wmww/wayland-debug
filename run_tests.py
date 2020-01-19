#!/usr/bin/python3

import unittest
import os
import sys

def change_to_correct_directory():
    project_path = os.path.dirname(os.path.realpath(__file__))
    current_path = os.path.realpath(os.getcwd())
    if project_path != current_path:
        print('Changing directory to ' + project_path + '…', file=sys.stderr)
        os.chdir(project_path)

def discover_recursive(suite, path):
    for i in os.listdir(path):
        sub = path + os.path.sep + i
        if os.path.isdir(sub):
            if os.path.basename(sub) == 'test':
                suite.addTest(unittest.TestLoader().discover(sub))
            else:
                discover_recursive(suite, sub)

def run_without_pytest():
    suite = unittest.TestSuite()
    root_path = os.path.realpath(os.getcwd())
    discover_recursive(suite, root_path)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    return result.wasSuccessful()

def run_with_pytest():
    import pytest
    result = pytest.main()
    return result == 0

def run_tests():
    change_to_correct_directory()
    try:
        success = run_with_pytest()
    except ModuleNotFoundError:
        success = run_without_pytest()
        print('\nInstall pytest for improved test output', file=sys.stderr)
    exit(0 if success else 1)

if __name__ == '__main__':
    run_tests()
else:
    raise RuntimeError('Not meant to be imported')
