import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals, cookies }) => {
	return {
		session: locals.session,
		user: locals.user,
		cookies: cookies.getAll(),
		subscriptions: ['retriever'] // stub — real subscription backend is follow-up work
	};
};
