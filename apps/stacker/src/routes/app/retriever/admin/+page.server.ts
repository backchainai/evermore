import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals, parent }) => {
	// Auth is handled by the portal layout (/app/+layout.server.ts).
	// Module access is handled by the retriever layout (/app/retriever/+layout.server.ts).

	// Admin role check — keep this even though portal handles auth
	if (locals.user && !locals.user.app_metadata?.is_admin) {
		redirect(303, '/app/retriever/chat');
	}
};
