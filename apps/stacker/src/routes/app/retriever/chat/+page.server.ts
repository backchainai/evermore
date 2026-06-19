import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
	// Auth is handled by the portal layout (/app/+layout.server.ts).
	// Module access is handled by the retriever layout (/app/retriever/+layout.server.ts).
};
