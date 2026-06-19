/**
 * Theme store — Svelte 5 runes-based state for portal theming.
 *
 * Persists theme selection to localStorage and applies data-theme
 * attribute to the document root. Works in tandem with the inline
 * script in app.html that prevents flash-of-wrong-theme on load.
 */

/** Available portal themes. Defined inline until Phase 2 creates shared types. */
export type PortalTheme = 'light' | 'dark' | 'neutral';

const VALID_THEMES: PortalTheme[] = ['light', 'dark', 'neutral'];
const STORAGE_KEY = 'portal-theme';
const DEFAULT_THEME: PortalTheme = 'light';

let currentTheme = $state<PortalTheme>(DEFAULT_THEME);

/** Returns the currently active theme. */
export function getTheme(): PortalTheme {
	return currentTheme;
}

/** Sets the active theme, updates the DOM attribute, and persists to localStorage. */
export function setTheme(name: PortalTheme): void {
	if (!VALID_THEMES.includes(name)) return;
	currentTheme = name;
	if (typeof document !== 'undefined') {
		document.documentElement.setAttribute('data-theme', name);
		localStorage.setItem(STORAGE_KEY, name);
	}
}

/** Initializes theme from localStorage on client-side mount. */
export function initTheme(): void {
	if (typeof localStorage === 'undefined') return;
	const stored = localStorage.getItem(STORAGE_KEY) as PortalTheme | null;
	if (stored && VALID_THEMES.includes(stored)) {
		currentTheme = stored;
	}
}
