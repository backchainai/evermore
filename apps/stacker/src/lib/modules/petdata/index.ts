import type { ModuleDefinition } from '$lib/portal/types';
import { PawPrint, ClipboardList } from '@lucide/svelte';

export const PETDATA_MODULE: Omit<ModuleDefinition, 'status'> & { status: 'active' } = {
	id: 'petdata',
	name: 'Pet Data',
	description: 'Behavioral observations and adoption profile data for shelter animals.',
	icon: PawPrint,
	basePath: '/app/petdata',
	status: 'active',
	navItems: [
		{ label: 'Animals', href: '/animals', icon: PawPrint },
		{ label: 'Notes', href: '/notes', icon: ClipboardList }
	]
};
