import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals }) => {
	if (!locals.session) {
		redirect(303, '/login');
	}

	return {
		subscriptions: ['retriever', 'petbio'] // stub — real subscription backend is follow-up work
	};
};
