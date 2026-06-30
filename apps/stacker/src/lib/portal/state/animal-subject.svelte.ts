/**
 * Animal-subject store — the persistent animal that follows the user across
 * modules (Evermore's signature). Svelte 5 runes module state, mirrored to
 * localStorage so the selection survives navigation and reloads.
 *
 * Mirrors the theme-store pattern: read via getAnimalSubject() inside a
 * reactive context; write via setAnimalSubject().
 */

export interface AnimalSubject {
	id: string;
	name: string;
}

const STORAGE_KEY = 'portal-animal-subject';

let subject = $state<AnimalSubject | null>(null);

/** Returns the currently selected animal subject, or null. */
export function getAnimalSubject(): AnimalSubject | null {
	return subject;
}

/** Sets (or clears) the active animal subject and persists to localStorage. */
export function setAnimalSubject(next: AnimalSubject | null): void {
	subject = next;
	if (typeof localStorage === 'undefined') return;
	if (next) {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
	} else {
		localStorage.removeItem(STORAGE_KEY);
	}
}

/** Restores the persisted animal subject on client-side mount. */
export function initAnimalSubject(): void {
	if (typeof localStorage === 'undefined') return;
	const raw = localStorage.getItem(STORAGE_KEY);
	if (!raw) return;
	try {
		const parsed = JSON.parse(raw) as AnimalSubject;
		if (parsed && typeof parsed.id === 'string' && typeof parsed.name === 'string') {
			subject = parsed;
		}
	} catch {
		// Ignore a malformed persisted value.
	}
}
