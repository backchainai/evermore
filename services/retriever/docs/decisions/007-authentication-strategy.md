---
adr: 7
title: Authentication Strategy
status: accepted
date: 2024-12-18
tags:
  - authentication
  - jwt
  - security
supersedes: null
superseded_by: null
related: [3]
---

# 007: Authentication Strategy

## Status

Accepted

## Context

Volunteers need to log in to use the Q&A system. Requirements:
- Simple authentication for MVP
- Future integration with existing volunteer management system
- Session management for conversation history

## Decision

**Simple JWT authentication** with design for future integration.

- Email/password login for MVP
- JWT tokens for session management
- User model includes `external_id` field for future SSO integration
- Auth logic isolated in `auth/` module for easy swap-out

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| OAuth immediately | Complex setup, unknown IdP requirements |
| No auth | Security risk, can't track usage per user |
| Session cookies only | Less flexible for future API consumers |
| Auth0/Clerk | External dependency, cost for MVP |

## Consequences

**Easier:**
- Quick to implement
- No external auth service dependency
- Full control over user model
- Easy to add admin users

**Harder:**
- Must implement password reset flow
- Security responsibility on us
- Manual user provisioning initially

## Implementation

```python
# User model with future integration field
class User(BaseModel):
    id: UUID
    email: str
    hashed_password: str
    external_id: str | None  # For future volunteer system integration
    is_active: bool
    created_at: datetime
```

## Future Integration

When integrating with volunteer management system:
1. Add SSO provider to auth module
2. Map `external_id` to volunteer system ID
3. Auto-provision users on first SSO login
4. Gradually deprecate password auth

## Security Measures

- Passwords hashed with bcrypt
- JWT tokens expire after 24 hours
- HTTPS required in production
- Rate limiting on login endpoint
