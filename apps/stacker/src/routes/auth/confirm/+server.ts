import { redirect } from '@sveltejs/kit';
import type { EmailOtpType } from '@supabase/supabase-js';
import type { RequestHandler } from './$types';

// Verifies the token_hash carried by a Supabase email link (invite, magic link,
// recovery, email change) and establishes the SSR cookie session. The invite
// template points here with `type=invite&next=/invite/accept` (lands on the
// set-password page); the magic-link template uses `type=magiclink&next=/app`
// (lands authenticated on the portal home). On any failure the user is sent to
// /auth/error, a neutral expired/invalid-link page. Only allow same-origin
// relative redirect targets to avoid an open redirect via a crafted `next`
// param (e.g. `//evil.com` or `/\evil.com`).
function safeNext(next: string | null): string {
	const fallback = '/app';
	if (!next || !next.startsWith('/') || next.startsWith('//') || next.startsWith('/\\')) {
		return fallback;
	}
	return next;
}

export const GET: RequestHandler = async ({ url, locals: { supabase } }) => {
	const tokenHash = url.searchParams.get('token_hash');
	const type = url.searchParams.get('type') as EmailOtpType | null;
	const next = safeNext(url.searchParams.get('next'));

	if (tokenHash && type) {
		const { error } = await supabase.auth.verifyOtp({ type, token_hash: tokenHash });
		if (!error) {
			redirect(303, next);
		}
	}

	redirect(303, '/auth/error');
};
