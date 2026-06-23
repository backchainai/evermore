import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ parent }) => {
	const { subscriptions } = await parent();
	return {
		moduleAccess: subscriptions.includes('retriever'),
		isAdmin: true // stub — check user role in real implementation
	};
};
