import { redirect } from '@sveltejs/kit';
import type { EmailOtpType } from '@supabase/supabase-js';
import type { RequestHandler } from './$types';

// Verifies the token_hash carried by a Supabase email link (invite, recovery,
// magic link, email change) and establishes the SSR cookie session. The invite
// email template points here with `type=invite&next=/invite/accept`, so an
// invited user lands authenticated on the set-password page. On any failure the
// user is sent to /invite/accept, which renders the invalid/expired state.
// Only allow same-origin relative redirect targets to avoid an open redirect
// via a crafted `next` param (e.g. `//evil.com` or `/\evil.com`).
function safeNext(next: string | null): string {
	const fallback = '/app/retriever/chat';
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

	redirect(303, '/invite/accept');
};
