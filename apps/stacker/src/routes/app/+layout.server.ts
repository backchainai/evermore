import { error, redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';
import { getActiveModule, isModuleEnabled } from '$lib/portal/config';

export const load: LayoutServerLoad = async ({ locals, url }) => {
	if (!locals.session) {
		redirect(303, '/login');
	}

	// Block direct navigation to a disabled module's routes (/app/<disabled>/*).
	const activeModule = getActiveModule(url.pathname);
	if (activeModule && !isModuleEnabled(activeModule.id)) {
		error(404, 'Module not available');
	}

	return {
		subscriptions: ['retriever', 'petdata'] // stub — real subscription backend is follow-up work
	};
};
