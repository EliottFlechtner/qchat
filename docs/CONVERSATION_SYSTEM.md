# Conversation Management System

This document describes the conversation management system that organizes messages between users.

## Overview

The conversation system automatically creates and manages conversations between pairs of users. Each conversation represents a bidirectional communication channel between exactly two users.

## Database Schema

### Conversation Table
- `id`: UUID primary key
- `user1_id`: UUID foreign key to users table
- `user2_id`: UUID foreign key to users table
- `created_at`: Timestamp when conversation was created
- `updated_at`: Timestamp when conversation was last modified

### Message Table Updates
- Added `conversation_id`: UUID foreign key to conversations table
- All messages must belong to a conversation

## Key Features

### Automatic Conversation Creation
- Conversations are automatically created when the first message is sent between two users
- The `ConversationService.get_or_create_conversation()` method handles this logic
- Users are ordered consistently (smaller UUID first) to prevent duplicate conversations

### Bidirectional Conversations
- Conversations are bidirectional - the order of participants doesn't matter
- A conversation between User A and User B is the same as between User B and User A
- Database queries use OR logic to find conversations regardless of user order

### Authorization
- Users can only access conversations they participate in
- All conversation and message endpoints verify user authorization
- Unauthorized access attempts are logged and rejected with 403 status

## API Endpoints

### GET /conversations/{username}
Retrieves all conversations for a user.

**Response:**
```json
{
  "conversations": [
    {
      "id": "uuid-string",
      "other_user": "username",
      "created_at": "2023-08-09T10:30:00Z",
      "updated_at": "2023-08-09T15:45:00Z"
    }
  ]
}
```

### GET /conversations/{username}/{conversation_id}/messages
Retrieves all messages in a specific conversation.

**Response:**
```json
{
  "conversation_id": "uuid-string",
  "messages": [
    {
      "sender": "username",
      "ciphertext": "base64-encrypted-content",
      "nonce": "base64-nonce",
      "encapsulated_key": "base64-kem-key",
      "signature": "base64-signature",
      "sent_at": "2023-08-09T10:30:00Z"
    }
  ]
}
```

### POST /send (Updated)
The existing send endpoint now automatically creates conversations.
- If no conversation exists between sender and recipient, one is created
- The message is linked to the conversation via `conversation_id`
- All existing functionality (WebSocket notifications, etc.) remains unchanged

### GET /inbox/{username} (Unchanged)
The inbox endpoint continues to work as before, retrieving undelivered messages.

## Service Layer

### ConversationService
- `get_or_create_conversation(user1_id, user2_id)`: Get existing or create new conversation
- `get_conversation_by_id(conversation_id)`: Retrieve conversation by ID
- `get_user_conversations(user_id)`: Get all conversations for a user
- `is_user_in_conversation(user_id, conversation_id)`: Check user authorization
- `get_other_user_in_conversation(user_id, conversation)`: Get the other participant

### MessageService (Updated)
- `send_message()`: Now creates/finds conversation automatically
- `get_conversation_messages()`: Retrieve messages for a specific conversation
- All existing methods remain unchanged

### UserService (Unchanged)
No changes required to the UserService.

## Security Considerations

1. **Authorization**: All conversation access is validated
2. **User Isolation**: Users can only see their own conversations
3. **Message Privacy**: Conversation messages maintain end-to-end encryption
4. **Audit Trail**: All unauthorized access attempts are logged

## Migration Notes

For existing deployments:
1. The database schema includes the new Conversation table
2. Existing messages will need conversation_id populated via migration
3. The migration should create conversations for all existing sender/recipient pairs
4. All existing API endpoints remain backward compatible

## Usage Examples

### Client fetching conversations:
```http
GET /conversations/alice
```

### Client fetching messages in a conversation:
```http
GET /conversations/alice/550e8400-e29b-41d4-a716-446655440000/messages
```

### Sending a message (creates conversation automatically):
```http
POST /send
{
  "sender": "alice",
  "recipient": "bob",
  "ciphertext": "...",
  "nonce": "...",
  "encapsulated_key": "...",
  "signature": "..."
}
```

This system provides a foundation for organized message management while maintaining the security and privacy features of the original design.
