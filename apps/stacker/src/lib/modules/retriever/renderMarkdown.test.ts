// @vitest-environment jsdom
import { describe, it, expect } from 'vitest';
import { renderMarkdown } from './renderMarkdown';

describe('renderMarkdown', () => {
	describe('neutralization', () => {
		it('removes <script> tags', () => {
			const out = renderMarkdown('<script>alert(1)</script>');
			expect(out).not.toContain('<script');
			expect(out).not.toContain('alert(1)');
		});

		it('strips onerror handlers and drops disallowed <img> tags', () => {
			const out = renderMarkdown('<img src=x onerror=alert(1)>');
			expect(out).not.toContain('onerror');
			expect(out).not.toContain('<img');
		});

		it('neutralizes a raw javascript: href', () => {
			const out = renderMarkdown('<a href="javascript:alert(1)">x</a>');
			expect(out).not.toContain('javascript:');
		});

		it('neutralizes a markdown link with a javascript: URL', () => {
			const out = renderMarkdown('[c](javascript:alert(1))');
			expect(out).not.toContain('javascript:');
		});

		it('strips event-handler attributes from allowed elements', () => {
			const out = renderMarkdown('<a href="https://x.com" onclick="alert(1)">x</a>');
			expect(out).toContain('<a');
			expect(out).not.toContain('onclick');
		});

		it('strips data-* attributes', () => {
			const out = renderMarkdown('<a href="https://x.com" data-x="y">z</a>');
			expect(out).not.toContain('data-x');
		});
	});

	describe('preservation', () => {
		it('renders headings', () => {
			expect(renderMarkdown('# H')).toContain('<h1');
		});

		it('renders unordered lists', () => {
			const out = renderMarkdown('- a\n- b');
			expect(out).toContain('<ul>');
			expect(out).toContain('<li>');
		});

		it('renders bold text', () => {
			expect(renderMarkdown('**b**')).toContain('<strong>');
		});

		it('renders italic text', () => {
			expect(renderMarkdown('*i*')).toContain('<em>');
		});

		it('renders inline code', () => {
			expect(renderMarkdown('`c`')).toContain('<code>');
		});

		it('renders fenced code blocks', () => {
			expect(renderMarkdown('```\nconst x = 1;\n```')).toContain('<pre>');
		});

		it('renders links with allowed https href', () => {
			const out = renderMarkdown('[x](https://example.com)');
			expect(out).toContain('<a href="https://example.com"');
		});
	});
});
