/**
 * Thin alias module over the generated OpenAPI types.
 *
 * Source of truth: `services/retriever/openapi.json` (committed by the backend).
 * Regenerate `types.generated.ts` with `npm run gen:types`; CI fails on drift.
 * These aliases preserve the names that downstream code imports.
 */
import type { components } from './types.generated';

type Schemas = components['schemas'];

export type AskRequest = Schemas['AskRequest'];
export type AskResponse = Schemas['AskResponse'];
export type ChunkWithScore = Schemas['ChunkWithScore'];
export type MessageResponse = Schemas['MessageResponse'];
export type MessageHistoryResponse = Schemas['MessageHistoryResponse'];
export type ClearHistoryResponse = Schemas['ClearHistoryResponse'];
export type DocumentResponse = Schemas['DocumentResponse'];
export type DocumentListResponse = Schemas['DocumentListResponse'];
export type DocumentUploadResponse = Schemas['DocumentUploadResponse'];
export type DocumentDeleteResponse = Schemas['DocumentDeleteResponse'];

// Enum-ish types not emitted as standalone schemas; derive from the parent.
export type ConfidenceLevel = Schemas['AskResponse']['confidence_level'];
export type MessageRole = Schemas['MessageResponse']['role'];
