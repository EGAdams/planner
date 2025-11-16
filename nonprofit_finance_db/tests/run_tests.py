#!/usr/bin/env python3
"""
Test runner script for nonprofit finance database
"""

import sys
import subprocess
import os
import time
import requests
import psutil # For gracefully terminating processes
from pathlib import Path

API_SERVER_URL = "http://localhost:8080"
API_PORT = 8080

def _wait_for_server_ready(url: str, timeout: int = 30) -> bool:
    """Waits for the API server to be ready."""
    for _ in range(timeout):
        try:
            response = requests.get(f"{url}/api", timeout=1)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    return False

def kill_process_on_port(port: int):
    """
    Kills any process listening on the specified port.
    """
    print(f"Attempting to kill any process on port {port}...")
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    print(f"  Found process {proc.name()} (PID: {proc.pid}) on port {port}. Killing...")
                    try:
                        proc.terminate()
                        proc.wait(timeout=5)
                        print(f"  Process {proc.pid} terminated.")
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        print(f"  Could not terminate process {proc.pid} gracefully, forcing kill.")
                        proc.kill()
                        proc.wait(timeout=5)
                        print(f"  Process {proc.pid} forcefully killed.")
                    except Exception as e:
                        print(f"  Error killing process {proc.pid}: {e}")
                    return # Assume only one process per port for simplicity in this context
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process may have terminated between iter and connections() call
            # Or we don't have permissions to access its connections
            pass
    print(f"No process found on port {port}.")


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

    # Set GEMINI_API_KEY for tests and prepare environment for subprocesses
    env = os.environ.copy()
    env["GEMINI_API_KEY"] = "test_gemini_api_key"
    # Ensure PYTHONPATH includes the project root for subprocesses
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{project_root}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = str(project_root)

    # Initialize the database
    print("Initializing database...")
    init_db_cmd = [sys.executable, 'scripts/init_db.py']
    init_db_result = subprocess.run(init_db_cmd, cwd=project_root, check=False, env=env)
    if init_db_result.returncode != 0:
        print("Error: Database initialization failed.")
        return False
    print("Database initialized.")

    server_process = None
    try:
        # Ensure the port is free before starting the server
        kill_process_on_port(API_PORT)

        # Start API server in the background
        print(f"Starting API server at {API_SERVER_URL}...")
        server_cmd = [sys.executable, '-m', 'uvicorn', 'api_server:app', '--host', '0.0.0.0', '--port', str(API_PORT)]
        server_process = subprocess.Popen(server_cmd, cwd=project_root, preexec_fn=os.setsid, env=env) # Pass env here
        
        if not _wait_for_server_ready(API_SERVER_URL):
            print(f"Error: API server not ready at {API_SERVER_URL} after 30 seconds.")
            return False
        print("API server is ready.")

        # Base pytest command
        cmd = [sys.executable, '-m', 'pytest', '--maxfail=1']

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

        print(f"Running command: {' '.join(cmd)}")
        print(f"Working directory: {os.getcwd()}")

        result = subprocess.run(cmd, check=False, env=env)
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: pytest not found. Make sure pytest is installed.")
        print("Run: pip install pytest pytest-cov")
        return False
    finally:
        if server_process:
            print("Stopping API server...")
            try:
                # Terminate the process group to ensure all child processes are killed
                os.killpg(os.getpgid(server_process.pid), subprocess.signal.SIGTERM)
                server_process.wait(timeout=5)
                print("API server stopped.")
            except (ProcessLookupError, subprocess.TimeoutExpired):
                print("API server did not terminate gracefully, forcing kill.")
                os.killpg(os.getpgid(server_process.pid), subprocess.signal.SIGKILL)
            except Exception as e:
                print(f"Error stopping API server: {e}")

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