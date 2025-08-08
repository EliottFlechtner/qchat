# Service Layer Architecture Documentation

## Overview

This document describes the refactored service layer architecture for the qchat backend server. The service layer separates business logic from HTTP route handlers, creating a more maintainable and testable codebase.

## Architecture

### Before Refactoring
- All business logic was mixed in route handlers
- Direct database queries in HTTP endpoints
- Global WebSocket client management
- Tight coupling between concerns
- Difficult to test business logic in isolation

### After Refactoring
- **Service Layer**: Handles all business logic
- **Route Layer**: Handles HTTP/WebSocket protocol concerns
- **Data Layer**: Database models and connections
- Clear separation of concerns
- Improved testability and maintainability

## Service Components

### 1. BaseService (`server/services/base.py`)
- Abstract base class for all services
- Provides common database session handling
- Foundation for dependency injection

```python
class BaseService(ABC):
    def __init__(self, db: Session):
        self.db = db
```

### 2. UserService (`server/services/user_service.py`)
Handles all user-related operations:
- **User registration** with cryptographic keys
- **User lookup** by username or UUID
- **Public key retrieval** for encryption
- **Username validation**

**Key Methods:**
- `create_user(username, kem_pk, sig_pk)` - Register new user
- `get_user_by_username(username)` - Find user by username
- `get_user_by_id(user_id)` - Find user by UUID
- `get_public_keys(username)` - Retrieve user's public keys
- `validate_username(username)` - Validate username format

### 3. MessageService (`server/services/message_service.py`)
Handles all message-related operations:
- **Message storage** with encryption components
- **Inbox retrieval** for users
- **Message delivery** tracking (consume-on-read pattern)
- **Cryptographic component validation**

**Key Methods:**
- `send_message(...)` - Store encrypted message
- `get_inbox_messages(user_id)` - Get undelivered messages
- `mark_messages_delivered(messages)` - Mark as delivered and delete
- `validate_message_components(...)` - Validate crypto components

### 4. WebSocketService (`server/services/websocket_service.py`)
Handles all WebSocket connection management:
- **Connection registry** for active users
- **Real-time notifications** to connected clients
- **Connection lifecycle** management
- **Graceful disconnection** handling

**Key Methods:**
- `add_client(user_id, websocket)` - Register new connection
- `remove_client(user_id)` - Remove connection
- `notify_user(user_id, message)` - Send notification
- `is_user_connected(user_id)` - Check connection status
- `get_connected_count()` - Get active connection count

## Route Layer Refactoring

### HTTP Routes (`server/routes/http_routes.py`)
Routes now focus solely on:
- HTTP protocol handling (request/response)
- Input validation and sanitization
- Service orchestration
- Error handling and status codes

**Example Before:**
```python
# Direct database queries mixed with business logic
def register_user(req: RegisterRequest, db: Session):
    existing_user = db.query(User).filter_by(username=username).first()
    if existing_user:
        return RegisterResponse(status="already_registered")

    new_user = User(...)
    db.add(new_user)
    db.commit()
    # ... more mixed concerns
```

**Example After:**
```python
# Clean separation: route handles HTTP, service handles business logic
def register_user(req: RegisterRequest, db: Session):
    user_service = UserService(db)
    if not user_service.validate_username(req.username):
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    success, status = user_service.create_user(username, req.kem_pk, req.sig_pk)
    return RegisterResponse(status=status)
```

### WebSocket Routes (`server/routes/ws_routes.py`)
Routes now focus on:
- WebSocket protocol handling
- Connection lifecycle management
- Service delegation for user management

## Benefits of the New Architecture

### 1. **Separation of Concerns**
- Routes handle protocol (HTTP/WebSocket)
- Services handle business logic
- Models handle data structure

### 2. **Improved Testability**
- Services can be unit tested in isolation
- Mock database sessions for testing
- Business logic independent of HTTP framework

### 3. **Better Maintainability**
- Single responsibility principle
- Easier to locate and modify business logic
- Reduced code duplication

### 4. **Enhanced Reusability**
- Services can be reused across different endpoints
- Business logic available for future CLI tools
- Easier to add new interfaces (GraphQL, gRPC, etc.)

### 5. **Cleaner Error Handling**
- Centralized business logic error handling
- Consistent error propagation
- Clear separation between business and protocol errors

## Usage Patterns

### Service Initialization
```python
# In route handlers
def my_endpoint(db: Session = Depends(get_db)):
    user_service = UserService(db)
    message_service = MessageService(db)
    # Use services...
```

### WebSocket Service (Singleton)
```python
# Global instance for WebSocket management
from server.services import websocket_service

# Use in routes
await websocket_service.notify_user(user_id, "new_message")
```

### Error Handling Pattern
```python
try:
    # Service calls
    result = user_service.create_user(...)
    return success_response(result)
except SQLAlchemyError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Database error")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

## File Structure

```
server/
├── services/                    # Service layer
│   ├── __init__.py             # Service exports
│   ├── base.py                 # Base service class
│   ├── user_service.py         # User business logic
│   ├── message_service.py      # Message business logic
│   └── websocket_service.py    # WebSocket management
├── routes/                     # Route layer (refactored)
│   ├── http_routes.py          # HTTP endpoints
│   └── ws_routes.py            # WebSocket endpoints
├── db/                         # Data layer
│   ├── database.py             # Database connection
│   └── database_models.py      # SQLAlchemy models
└── utils/                      # Utility functions
    └── logger.py               # Logging configuration
```

## Migration Notes

### Breaking Changes
- Removed global `connected_clients` dictionary from routes
- WebSocket management now centralized in service layer
- Database queries moved from routes to services

### Compatibility
- All HTTP endpoints maintain same request/response contracts
- WebSocket protocol unchanged for clients
- Database schema unchanged

## Future Enhancements

With the service layer in place, future improvements become easier:

1. **Testing**: Add comprehensive unit tests for each service
2. **Caching**: Add Redis caching layer in services
3. **Metrics**: Add business logic metrics and monitoring
4. **Validation**: Enhanced input validation in services
5. **CLI Tools**: Reuse services for command-line administration
6. **Background Jobs**: Use services in task queues
7. **API Versioning**: Multiple route versions using same services

## Best Practices

1. **Service Initialization**: Always initialize services with database session
2. **Error Propagation**: Let SQLAlchemy errors bubble up to routes
3. **Logging**: Use consistent logging patterns in services
4. **Validation**: Validate inputs in services, not just routes
5. **Transactions**: Handle database transactions in services
6. **Documentation**: Keep service methods well-documented
