/**
 * Thin alias module over the generated OpenAPI types.
 *
 * Source of truth: `services/petdata/openapi.json` (committed by the backend).
 * Regenerate `types.generated.ts` with `npm run gen:types`; CI fails on drift.
 * These aliases preserve the names that downstream code imports.
 */
import type { components } from './types.generated';

type Schemas = components['schemas'];

export type Animal = Schemas['AnimalResponse'];
export type VolunteerNote = Schemas['VolunteerNoteResponse'];
export type BehaviorProfile = Schemas['BehaviorProfileResponse'];
export type StaffAssessment = Schemas['StaffAssessmentResponse'];
export type AnimalListResponse = Schemas['AnimalListResponse'];
export type AnimalDetailResponse = Schemas['AnimalDetailResponse'];
