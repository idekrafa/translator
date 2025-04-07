# Book Translation API Tests

This directory contains tests for the Book Translation API. The tests are organized by type and module.

## Test Structure

- `api/`: Tests for API endpoints
- `services/`: Tests for service functions
- `test_end_to_end.py`: End-to-end tests that simulate complete user flows
- `conftest.py`: Shared test fixtures and mocks

## Running Tests

The simplest way to run all tests is using the `run_tests.py` script in the root directory:

```bash
# Navigate to the backend directory
cd backend

# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --unit

# Run only API tests
python run_tests.py --api

# Run only end-to-end tests
python run_tests.py --e2e

# Generate coverage report
python run_tests.py --coverage

# Generate HTML report
python run_tests.py --html
```

Alternatively, you can use pytest directly:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_end_to_end.py

# Run tests with specific marker
pytest -m unit
```

## Test Categories

Tests are organized into several categories using pytest marks:

- `unit`: Tests for individual functions and components
- `api`: Tests for API endpoints
- `e2e`: End-to-end tests for complete user flows
- `asyncio`: Tests for asynchronous functions

## Mock Setup

The tests use mocks to avoid making actual API calls or performing actual file operations:

- Translation API calls are mocked in `conftest.py`
- File operations use in-memory buffers where possible
- UUIDs are patched for deterministic testing

## Environment Setup

The tests automatically set up the required environment:

- Test directories are created if they don't exist
- A mock OpenAI API key is used to avoid using a real key
- Temporary files are cleaned up after tests

## Writing New Tests

When writing new tests, follow these guidelines:

1. Use the appropriate test category marker
2. Create fixtures for reusable setup
3. Mock external dependencies
4. Clean up any created files or resources
5. Follow the existing test patterns 