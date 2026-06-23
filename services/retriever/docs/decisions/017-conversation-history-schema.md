---
adr: 017
title: Conversation History Schema
status: accepted
date: 2024-12-19
tags: [database, conversation, mvp]
supersedes: null
superseded_by: null
related: [007-authentication-strategy]
---

# 017: Conversation History Schema

## Status

Accepted

## Context

Increment 8 adds persistent conversation history so users can have multi-turn conversations and see past Q&A when returning to the app. We needed to decide:

1. How to structure the database schema for storing messages
2. Whether to enforce referential integrity between messages and users
3. How to handle conversation grouping and limits

## Decision

We implemented a simplified MVP schema:

### Single `messages` table without foreign key constraint

```sql
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_user_created ON messages(user_id, created_at);
```

Key decisions:

1. **No foreign key to users table**: The `user_id` column stores the user's UUID but doesn't enforce a FK constraint to `users.id`. This prevents errors when:
   - Database is recreated while JWT sessions persist
   - Testing with mock user IDs
   - Future anonymous user support

2. **No separate conversations table**: All messages for a user are treated as a single implicit conversation. This avoids:
   - Complex conversation management UI
   - Conversation ID generation and tracking
   - Join queries

3. **Message count limit (20)**: Conversation context is limited by message count rather than token estimation. Simpler to implement and sufficient for MVP.

4. **Messages module**: MessageStore lives in `backend/src/retriever/modules/messages/` as a dedicated module for conversation history management.

## Alternatives Considered

### Two-table design with FK constraint
```sql
CREATE TABLE conversations (id, user_id, title, created_at);
CREATE TABLE messages (id, conversation_id REFERENCES conversations(id), ...);
```

**Rejected because:**
- Adds complexity without immediate value
- Requires conversation management UI
- MVP doesn't need multiple conversations per user

### Foreign key constraint on user_id
```sql
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
```

**Rejected because:**
- Causes errors during development when DB is recreated
- SQLite doesn't support ALTER TABLE DROP CONSTRAINT for migration
- Application-layer validation is sufficient for MVP
- Can be added later with proper migration tooling

### Token-based context limits
**Rejected because:**
- Requires token counting/estimation
- Adds complexity
- Message count (20) is simpler and works within LLM context limits

## Consequences

### Positive
- Simple schema, easy to understand and maintain
- No FK constraint errors during development
- Straightforward migration path to multi-conversation support
- Fast queries with indexed user_id + created_at

### Negative
- No database-enforced referential integrity
- Orphan messages possible if user deleted without cleanup
- Single implicit conversation per user (no conversation switching)

### Migration Path

When multi-conversation support is needed:
1. Add `conversations` table
2. Add nullable `conversation_id` to messages
3. Backfill existing messages with one conversation per user
4. Add FK constraint with proper migration tooling
5. Update UI for conversation management

This approach allows zero-downtime, backward-compatible evolution.
