import { type Handle, redirect } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';
import { createSupabaseServerClient } from '$lib/server/supabase';

const supabaseHandle: Handle = async ({ event, resolve }) => {
	event.locals.supabase = createSupabaseServerClient(event.cookies);

	event.locals.safeGetSession = async () => {
		const {
			data: { session }
		} = await event.locals.supabase.auth.getSession();
		if (!session) {
			return { session: null, user: null };
		}
		const {
			data: { user },
			error
		} = await event.locals.supabase.auth.getUser();
		if (error) {
			return { session: null, user: null };
		}
		return { session, user };
	};

	return resolve(event, {
		filterSerializedResponseHeaders(name) {
			return name === 'content-range' || name === 'x-supabase-api-version';
		}
	});
};

const protectedPaths = ['/app'];

const authGuard: Handle = async ({ event, resolve }) => {
	const { session, user } = await event.locals.safeGetSession();
	event.locals.session = session;
	event.locals.user = user;

	const isProtected = protectedPaths.some((p) => event.url.pathname.startsWith(p));

	if (!session && isProtected) {
		redirect(303, '/login');
	}

	if (session && event.url.pathname === '/login') {
		redirect(303, '/app');
	}

	return resolve(event);
};

// Strict Content-Security-Policy shipped in Report-Only mode. It is intentionally
// not enforcing: SvelteKit injects inline hydration scripts (an enforcing
// `script-src 'self'` would break hydration without SvelteKit's hash/nonce
// integration), and Supabase JS connects to a per-environment external URL
// (an enforcing `connect-src 'self'` would break auth). Report-Only collects
// violation reports while the enforcing migration (SvelteKit `kit.csp`) lands.
// See docs/adr/0032-supabase-auth-cookie-non-httponly.md.
const CONTENT_SECURITY_POLICY_REPORT_ONLY = [
	"default-src 'self'",
	"base-uri 'self'",
	"object-src 'none'",
	"frame-ancestors 'self'",
	"form-action 'self'",
	"img-src 'self' data:",
	"font-src 'self'",
	"style-src 'self' 'unsafe-inline'",
	"script-src 'self'",
	"connect-src 'self' https:"
].join('; ');

// Compensating controls for the non-HttpOnly Supabase auth cookie (ADR 0032 (supabase-auth-cookie-non-httponly)):
// hardening headers plus a Report-Only CSP set on every response.
const securityHeaders: Handle = async ({ event, resolve }) => {
	const response = await resolve(event);
	response.headers.set('X-Content-Type-Options', 'nosniff');
	response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
	response.headers.set('X-Frame-Options', 'DENY');
	response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
	response.headers.set('Content-Security-Policy-Report-Only', CONTENT_SECURITY_POLICY_REPORT_ONLY);
	return response;
};

export const handle: Handle = sequence(supabaseHandle, authGuard, securityHeaders);
