import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

// An invited user reaches this page already authenticated, via the session that
// /auth/confirm established from their invite link. Without that session there is
// no valid invitation, so the page renders an invalid/expired state instead.
export const load: PageServerLoad = async ({ locals }) => {
	return { invited: Boolean(locals.session), email: locals.user?.email ?? null };
};

export const actions: Actions = {
	default: async ({ request, locals: { session, supabase } }) => {
		if (!session) {
			return fail(401, { error: 'Your invitation link is invalid or has expired.' });
		}

		const formData = await request.formData();
		const password = formData.get('password') as string;
		const confirm = formData.get('confirm') as string;

		if (!password || !confirm) {
			return fail(400, { error: 'Please enter and confirm your password.' });
		}
		if (password.length < 8) {
			return fail(400, { error: 'Password must be at least 8 characters.' });
		}
		if (password !== confirm) {
			return fail(400, { error: 'Passwords do not match.' });
		}

		const { error } = await supabase.auth.updateUser({ password });
		if (error) {
			return fail(400, { error: error.message });
		}

		redirect(303, '/app/retriever/chat');
	}
};
