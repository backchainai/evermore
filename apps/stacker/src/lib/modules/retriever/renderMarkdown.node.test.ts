// @vitest-environment node
import { describe, it, expect } from 'vitest';
import { renderMarkdown } from './renderMarkdown';

describe('renderMarkdown (node/SSR, no DOM)', () => {
	it('fails closed: escapes content instead of returning raw/sanitized HTML', () => {
		const out = renderMarkdown('<img src=x onerror=alert(1)>');
		// The whole payload is HTML-escaped (not parsed), so no live <img> tag or
		// onerror attribute can ever reach the DOM: this is plain inert text.
		expect(out).not.toContain('<img');
		expect(out).toContain('&lt;img');
		expect(out).not.toMatch(/<[a-z]/i);
	});
});
