---
name: adr-example
description: Read when writing your first ADR. Shows completed Redis caching decision as example.
category: decision
when_to_use:
- Reference when writing your first ADR
---
# 1. Use Redis for Caching

Date: 2025-01-15
Status: Accepted

## Context

API response times exceed 500ms for user profile queries.
80% of queries are repeat reads within 5 minutes.

## Decision

Use Redis for caching user profiles and session data.
TTL: 5 minutes for profiles, 24 hours for sessions.

## Consequences

**Positive**:
- Expected 60% reduction in database queries
- Sub-100ms response for cached data

**Negative**:
- Additional infrastructure dependency
- Cache invalidation complexity for profile updates

**Migration**:
Add Redis container to docker-compose, implement
cache-aside pattern starting with user profiles.
