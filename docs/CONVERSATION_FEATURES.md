# Conversation Feature Usage Guide

This document explains how to use the new conversation features in the qchat client.

## Overview

The qchat client now supports conversation-based messaging, allowing users to:
- List all their conversations
- View messages in specific conversations
- Send messages within conversation contexts
- Manage conversation history

## New API Endpoints

The following new endpoints have been added to the server:

### 1. Get User Conversations
```
GET /conversations/{username}
```
Returns all conversations for a user with metadata.

### 2. Get Conversation Messages
```
GET /conversations/{username}/{conversation_id}/messages
```
Returns all messages in a specific conversation.

## Client API Functions

New functions have been added to `client/api.py`:

### `get_conversations(username: str)`
Fetches all conversations for a user.

**Parameters:**
- `username`: Username whose conversations to retrieve

**Returns:**
- List of conversation dictionaries

### `get_conversation_messages(username: str, conversation_id: str)`
Fetches all messages in a specific conversation.

**Parameters:**
- `username`: Username requesting the messages
- `conversation_id`: UUID of the conversation

**Returns:**
- List of message dictionaries

## Client Service Functions

New service functions have been added to `client/services/conversation.py`:

### `fetch_user_conversations(username: str)`
High-level function to fetch conversations with error handling.

### `fetch_conversation_messages(username, conversation_id, decrypt=False, kem_sk=None, sig_pk_cache=None)`
High-level function to fetch and optionally decrypt conversation messages.

### `get_or_create_conversation_id(username: str, other_user: str)`
Finds the conversation ID between two users.

## CLI Usage

### Conversation CLI

A new conversation CLI has been created at `client/conversation_cli.py`:

```bash
# Interactive mode
python -m client.conversation_cli <username>

# List conversations
python -m client.conversation_cli <username> list

# View conversation with another user
python -m client.conversation_cli <username> view <other_user>

# Send a message
python -m client.conversation_cli <username> send <other_user> <message>

# Interactive menu
python -m client.conversation_cli <username> menu
```

### Updated Main Client

The main client (`client/main.py`) now supports two modes:

```bash
# Direct chat mode (original functionality)
python client/main.py <username> <recipient>

# Conversation management mode (new)
python client/main.py <username>
```

## Example Usage

### 1. List Your Conversations
```bash
python -m client.conversation_cli alice list
```

### 2. View Conversation with Bob
```bash
python -m client.conversation_cli alice view bob
```

### 3. Send Message to Bob
```bash
python -m client.conversation_cli alice send bob "Hello Bob!"
```

### 4. Interactive Mode
```bash
python -m client.conversation_cli alice
```
This opens an interactive menu with options to:
- List all conversations
- View specific conversations
- Send messages
- Exit

## Response Formats

### Conversation Response
```json
{
  "id": "conversation-uuid",
  "other_user": "username",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:30:00Z"
}
```

### Message Response
```json
{
  "sender": "username",
  "ciphertext": "base64-encoded-ciphertext",
  "nonce": "base64-encoded-nonce",
  "encapsulated_key": "base64-encoded-key",
  "signature": "base64-encoded-signature",
  "sent_at": "2024-01-01T12:00:00Z"
}
```

## Features

### Message Decryption
The conversation service can automatically decrypt messages if you provide:
- Your KEM secret key
- Cache of sender public keys for signature verification

### Signature Verification
Messages can be verified for authenticity using the sender's public key.

### Error Handling
All functions include comprehensive error handling and graceful degradation.

## Integration

The conversation features integrate seamlessly with the existing:
- Message sending (`send_encrypted_message`)
- User registration (`login_or_register`)
- WebSocket notifications
- Cryptographic operations

## Future Enhancements

Potential improvements include:
- Conversation creation endpoints
- Message search within conversations
- Conversation metadata management
- Read receipts and message status
- Message pagination for large conversations
