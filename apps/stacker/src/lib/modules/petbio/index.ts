import type { ModuleDefinition } from '$lib/portal/types';
import { PawPrint, ClipboardList } from '@lucide/svelte';

export const PETBIO_MODULE: Omit<ModuleDefinition, 'status'> & { status: 'active' } = {
	id: 'petbio',
	name: 'PetBio',
	description: 'Behavioral observations and adoption profile data for shelter animals.',
	icon: PawPrint,
	basePath: '/app/petbio',
	status: 'active',
	navItems: [
		{ label: 'Animals', href: '/animals', icon: PawPrint },
		{ label: 'Notes', href: '/notes', icon: ClipboardList }
	]
};
