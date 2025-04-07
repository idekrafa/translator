#!/usr/bin/env python3
"""
Test runner script for the Book Translation API.
Sets up the test environment and runs the tests.
"""
import os
import sys
import subprocess
import argparse

def setup_test_env():
    """Set up the test environment with required variables"""
    # Set test API key to avoid using real one
    os.environ["OPENAI_API_KEY"] = "sk-test-key-for-pytest"
    
    # Set other environment variables needed for testing
    os.environ["PYTHONPATH"] = os.path.abspath(os.path.dirname(__file__))
    
    # Create necessary directories
    os.makedirs("output", exist_ok=True)
    os.makedirs("test_output", exist_ok=True)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run tests for the Book Translation API")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--api", action="store_true", help="Run only API tests")
    parser.add_argument("--e2e", action="store_true", help="Run only end-to-end tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    return parser.parse_args()

def main():
    """Main function to run the tests"""
    # Parse arguments
    args = parse_args()
    
    # Set up test environment
    setup_test_env()
    
    # Construct pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add markers based on arguments
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.api:
        cmd.extend(["-m", "api"])
    elif args.e2e:
        cmd.extend(["-m", "e2e"])
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=term"])
        if args.html:
            cmd.append("--cov-report=html")
    
    # Add HTML report if requested
    if args.html and not args.coverage:
        cmd.append("--html=test-report.html")
    
    # Run the tests
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    # Return the exit code
    return result.returncode

if __name__ == "__main__":
    sys.exit(main()) 