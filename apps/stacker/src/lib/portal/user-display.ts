/** Helpers for deriving display strings from a user's email address. */

function emailLocalParts(email: string): string[] {
	return email
		.split('@')[0]
		.split(/[._-]/)
		.filter(Boolean);
}

/** Two-letter initials from an email (e.g. "chris.krough" → "CK"). */
export function initialsFromEmail(email: string | null | undefined): string {
	if (!email) return '?';
	const parts = emailLocalParts(email);
	if (parts.length >= 2) {
		return (parts[0][0] + parts[1][0]).toUpperCase();
	}
	return email.substring(0, 2).toUpperCase();
}

/** Title-cased display name from an email (e.g. "chris.krough" → "Chris Krough"). */
export function displayNameFromEmail(email: string | null | undefined): string {
	if (!email) return 'Account';
	const parts = emailLocalParts(email);
	const titled = parts.map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(' ');
	return titled || email.split('@')[0];
}

/** First name from an email (e.g. "chris.krough" → "Chris"). */
export function firstNameFromEmail(email: string | null | undefined, fallback = 'there'): string {
	if (!email) return fallback;
	const first = emailLocalParts(email)[0];
	return first ? first.charAt(0).toUpperCase() + first.slice(1) : fallback;
}
