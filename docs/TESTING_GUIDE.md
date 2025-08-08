# Testing Guide for QChat Service Layer

## Overview

This guide explains how to run and understand the tests for the newly implemented service layer in the QChat backend.

## Test Structure

```
tests/
├── __init__.py              # Makes tests a Python package
├── conftest.py              # Pytest configuration and fixtures
├── test_config.py           # Existing configuration tests
└── test_services.py         # New service layer tests
```

## Running Tests

### Prerequisites

1. **Install test dependencies** (if not already installed):
   ```bash
   pip install pytest pytest-asyncio pytest-mock
   ```

2. **From the project root directory** (`/home/shark/Documents/qchat`):

### Quick Commands

```bash
# Run all service tests
python -m pytest tests/test_services.py -v

# Run specific test class
python -m pytest tests/test_services.py::TestUserService -v

# Run specific test method
python -m pytest tests/test_services.py::TestUserService::test_create_user_success -v

# Run all tests with coverage (if pytest-cov is installed)
python -m pytest tests/ --cov=server/services --cov-report=term-missing

# Use the test runner script
./run_tests.sh
```

### Docker Environment

If you're running in Docker, you can run tests like this:
```bash
# From inside the Docker container
python -m pytest tests/test_services.py -v
```

## Test Cases Explained

### UserService Tests

#### `test_create_user_success`
- **Purpose**: Verifies that new users can be created successfully
- **Mocks**: Database session with no existing user
- **Assertions**: Success status, "registered" response, database operations called

#### `test_create_user_already_exists`
- **Purpose**: Handles duplicate registration attempts
- **Mocks**: Database session with existing user
- **Assertions**: Success status, "already_registered" response, no database writes

#### `test_validate_username`
- **Purpose**: Tests username validation logic
- **Tests**: Valid usernames, empty strings, whitespace-only strings
- **Assertions**: Boolean validation results

#### `test_get_public_keys_success`
- **Purpose**: Retrieves user's cryptographic public keys
- **Mocks**: Database with user having public keys
- **Assertions**: Correct key tuple returned

#### `test_get_public_keys_user_not_found`
- **Purpose**: Handles requests for non-existent users
- **Mocks**: Database with no matching user
- **Assertions**: None returned

### MessageService Tests

#### `test_validate_message_components`
- **Purpose**: Validates required cryptographic components
- **Tests**: Complete components, missing components (each field)
- **Assertions**: Boolean validation results

#### `test_send_message_success`
- **Purpose**: Tests message storage functionality
- **Mocks**: Database session and Message model constructor
- **Assertions**: Message ID returned, database operations called

#### `test_get_inbox_messages`
- **Purpose**: Tests inbox message retrieval
- **Mocks**: Database query returning mock messages
- **Assertions**: Correct messages returned, proper query filters

### WebSocketService Tests

#### `test_add_and_remove_client`
- **Purpose**: Tests WebSocket connection lifecycle
- **Tests**: Adding connections, checking status, removing connections
- **Assertions**: Connection counts, status checks, client retrieval

#### `test_notify_user_success` (Async)
- **Purpose**: Tests successful user notification
- **Mocks**: WebSocket with AsyncMock for send_text
- **Assertions**: Success status, correct method calls

#### `test_notify_user_not_connected` (Async)
- **Purpose**: Tests notification to disconnected user
- **Tests**: Notification attempt with no active connection
- **Assertions**: Failure status returned

## Test Configuration

### Pytest Configuration (`pytest.ini`)
```ini
[pytest]
asyncio_mode = auto          # Automatically handle async tests
addopts = -v --tb=short     # Verbose output, short tracebacks
testpaths = tests           # Look for tests in tests/ directory
```

### Fixtures (`conftest.py`)

#### `mock_db`
- Provides a mocked database session for all tests
- Usage: `def test_something(mock_db): ...`

#### `mock_user`
- Provides a pre-configured mock user object
- Includes ID, username, and public keys
- Usage: `def test_something(mock_user): ...`

#### `mock_message`
- Provides a pre-configured mock message object
- Includes all required message fields
- Usage: `def test_something(mock_message): ...`

## Understanding Test Results

### Successful Test Output
```
tests/test_services.py::TestUserService::test_create_user_success PASSED [7%]
tests/test_services.py::TestUserService::test_validate_username PASSED [14%]
...
================================== 12 passed in 0.15s ==================================
```

### Failed Test Output
```
FAILED tests/test_services.py::TestUserService::test_create_user_success - AssertionError: assert False is True
```

### Common Issues and Solutions

#### Import Errors
```
ModuleNotFoundError: No module named 'server'
```
**Solution**: The test files include path manipulation to handle imports:
```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

#### Async Test Failures
```
async def functions are not natively supported
```
**Solution**: Tests are marked with `@pytest.mark.asyncio` and use `AsyncMock`

#### Mock Issues
```
AttributeError: Mock object has no attribute 'some_method'
```
**Solution**: Configure mocks properly:
```python
mock_db.query.return_value.filter_by.return_value.first.return_value = mock_user
```

## Adding New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Example New Test
```python
def test_new_feature(mock_db):
    """Test description."""
    # Arrange
    service = SomeService(mock_db)

    # Act
    result = service.some_method("input")

    # Assert
    assert result == expected_value
    mock_db.some_operation.assert_called_once()
```

### Async Test Example
```python
@pytest.mark.asyncio
async def test_async_feature():
    """Test async functionality."""
    # Arrange
    mock_websocket = Mock()
    mock_websocket.send_text = AsyncMock()

    # Act
    result = await service.notify(user_id, "message")

    # Assert
    assert result is True
    mock_websocket.send_text.assert_called_once()
```

## Benefits of the Test Suite

1. **Isolated Testing**: Services can be tested without database or network dependencies
2. **Fast Execution**: Mocked dependencies make tests run quickly
3. **Clear Documentation**: Tests serve as usage examples for the service layer
4. **Regression Prevention**: Automated tests catch breaking changes
5. **Refactoring Safety**: Tests ensure functionality remains intact during changes

## Next Steps

1. **Add Integration Tests**: Test services with real database connections
2. **Add Performance Tests**: Measure service performance under load
3. **Add Property-Based Tests**: Use hypothesis for more comprehensive testing
4. **Add Test Coverage**: Ensure all service methods are tested
5. **Add Continuous Integration**: Run tests automatically on code changes
