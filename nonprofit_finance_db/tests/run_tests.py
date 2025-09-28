#!/usr/bin/env python3
"""
Test runner script for nonprofit finance database
"""

import sys
import subprocess
import os
from pathlib import Path

def run_tests(test_type='all', verbose=False, coverage=False):
    """
    Run tests for the nonprofit finance database

    Args:
        test_type: Type of tests to run ('all', 'unit', 'integration', 'parsers', 'detection', 'ingestion')
        verbose: Enable verbose output
        coverage: Enable coverage reporting
    """

    # Get the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Base pytest command
    cmd = ['python', '-m', 'pytest']

    # Add test paths based on test type
    if test_type == 'all':
        cmd.append('tests/')
    elif test_type == 'parsers':
        cmd.append('tests/test_parsers.py')
    elif test_type == 'detection':
        cmd.append('tests/test_detection.py')
    elif test_type == 'ingestion':
        cmd.append('tests/test_ingestion.py')
    elif test_type == 'unit':
        cmd.extend(['-m', 'unit'])
    elif test_type == 'integration':
        cmd.extend(['-m', 'integration'])
    else:
        print(f"Unknown test type: {test_type}")
        return False

    # Add options
    if verbose:
        cmd.append('-v')

    if coverage:
        cmd.extend(['--cov=.', '--cov-report=term-missing'])

    # Run tests
    print(f"Running command: {' '.join(cmd)}")
    print(f"Working directory: {os.getcwd()}")

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: pytest not found. Make sure pytest is installed.")
        print("Run: pip install pytest pytest-cov")
        return False

def main():
    """Main entry point for test runner"""
    import argparse

    parser = argparse.ArgumentParser(description='Run tests for nonprofit finance database')
    parser.add_argument(
        'test_type',
        nargs='?',
        default='all',
        choices=['all', 'unit', 'integration', 'parsers', 'detection', 'ingestion'],
        help='Type of tests to run'
    )
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-c', '--coverage', action='store_true', help='Enable coverage reporting')

    args = parser.parse_args()

    print("=" * 60)
    print("Nonprofit Finance Database - Test Runner")
    print("=" * 60)

    success = run_tests(args.test_type, args.verbose, args.coverage)

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()