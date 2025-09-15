#!/usr/bin/env python3
"""Test runner script for Legal Simulation Platform.

This script provides a comprehensive test runner with different test categories
and reporting options for the Legal Simulation Platform.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def install_test_dependencies() -> int:
    """Install test dependencies."""
    print("Installing test dependencies...")
    return run_command([
        sys.executable, "-m", "pip", "install", "-r", "tests/requirements-test-lite.txt"
    ])


def run_unit_tests(verbose: bool = False) -> int:
    """Run unit tests."""
    print("Running unit tests...")
    cmd = ["python", "-m", "pytest", "tests/unit/"]
    if verbose:
        cmd.append("-v")
    return run_command(cmd)


def run_integration_tests(verbose: bool = False) -> int:
    """Run integration tests."""
    print("Running integration tests...")
    cmd = ["python", "-m", "pytest", "tests/integration/"]
    if verbose:
        cmd.append("-v")
    return run_command(cmd)


def run_determinism_tests(verbose: bool = False) -> int:
    """Run determinism tests."""
    print("Running determinism tests...")
    cmd = ["python", "-m", "pytest", "tests/determinism/"]
    if verbose:
        cmd.append("-v")
    return run_command(cmd)


def run_compliance_tests(verbose: bool = False) -> int:
    """Run compliance tests."""
    print("Running compliance tests...")
    cmd = ["python", "-m", "pytest", "tests/compliance/"]
    if verbose:
        cmd.append("-v")
    return run_command(cmd)


def run_performance_tests(verbose: bool = False, parallel: bool = False) -> int:
    """Run performance tests."""
    print("Running performance tests...")
    cmd = ["python", "-m", "pytest", "tests/performance/"]
    if verbose:
        cmd.append("-v")
    if parallel:
        cmd.extend(["-n", "auto"])
    return run_command(cmd)


def run_e2e_tests(verbose: bool = False) -> int:
    """Run end-to-end tests."""
    print("Running end-to-end tests...")
    cmd = ["python", "-m", "pytest", "tests/e2e/"]
    if verbose:
        cmd.append("-v")
    return run_command(cmd)


def run_all_tests(verbose: bool = False, parallel: bool = False) -> int:
    """Run all tests."""
    print("Running all tests...")
    cmd = ["python", "-m", "pytest", "tests/"]
    if verbose:
        cmd.append("-v")
    if parallel:
        cmd.extend(["-n", "auto"])
    return run_command(cmd)


def run_coverage_report() -> int:
    """Generate coverage report."""
    print("Generating coverage report...")
    return run_command([
        "python", "-m", "pytest", "--cov=services", "--cov-report=html", "--cov-report=term"
    ])


def run_specific_test(test_path: str, verbose: bool = False) -> int:
    """Run a specific test file or test function."""
    print(f"Running specific test: {test_path}")
    cmd = ["python", "-m", "pytest", test_path]
    if verbose:
        cmd.append("-v")
    return run_command(cmd)


def run_linting() -> int:
    """Run code linting and formatting checks."""
    print("Running linting and formatting checks...")
    
    # Run black check
    black_exit = run_command([sys.executable, "-m", "black", "--check", "services/"])
    
    # Run isort check
    isort_exit = run_command([sys.executable, "-m", "isort", "--check-only", "services/"])
    
    # Run flake8
    flake8_exit = run_command([sys.executable, "-m", "flake8", "services/"])
    
    # Run mypy
    mypy_exit = run_command([sys.executable, "-m", "mypy", "services/"])
    
    return max(black_exit, isort_exit, flake8_exit, mypy_exit)


def run_security_checks() -> int:
    """Run security checks."""
    print("Running security checks...")
    
    # Run bandit
    bandit_exit = run_command([sys.executable, "-m", "bandit", "-r", "services/"])
    
    # Run safety
    safety_exit = run_command([sys.executable, "-m", "safety", "check"])
    
    return max(bandit_exit, safety_exit)


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Legal Simulation Platform Test Runner")
    
    parser.add_argument(
        "test_type",
        choices=[
            "unit", "integration", "determinism", "compliance", 
            "performance", "e2e", "all", "coverage", "lint", "security", "install"
        ],
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "-p", "--parallel",
        action="store_true",
        help="Run tests in parallel (for performance tests)"
    )
    
    parser.add_argument(
        "--test-path",
        type=str,
        help="Specific test file or function to run"
    )
    
    args = parser.parse_args()
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    exit_code = 0
    
    try:
        if args.test_type == "install":
            exit_code = install_test_dependencies()
        elif args.test_type == "unit":
            exit_code = run_unit_tests(args.verbose)
        elif args.test_type == "integration":
            exit_code = run_integration_tests(args.verbose)
        elif args.test_type == "determinism":
            exit_code = run_determinism_tests(args.verbose)
        elif args.test_type == "compliance":
            exit_code = run_compliance_tests(args.verbose)
        elif args.test_type == "performance":
            exit_code = run_performance_tests(args.verbose, args.parallel)
        elif args.test_type == "e2e":
            exit_code = run_e2e_tests(args.verbose)
        elif args.test_type == "all":
            exit_code = run_all_tests(args.verbose, args.parallel)
        elif args.test_type == "coverage":
            exit_code = run_coverage_report()
        elif args.test_type == "lint":
            exit_code = run_linting()
        elif args.test_type == "security":
            exit_code = run_security_checks()
        elif args.test_path:
            exit_code = run_specific_test(args.test_path, args.verbose)
        
        if exit_code == 0:
            print(f"\n✅ {args.test_type.title()} tests completed successfully!")
        else:
            print(f"\n❌ {args.test_type.title()} tests failed with exit code {exit_code}")
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        exit_code = 130
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
