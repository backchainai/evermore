import type { ModuleDefinition } from '$lib/portal/types';
import { MessageSquare, FileText, Search } from '@lucide/svelte';

export const RETRIEVER_MODULE: Omit<ModuleDefinition, 'status'> & { status: 'active' } = {
	id: 'retriever',
	name: 'Retriever',
	description: "AI Q&A from your shelter's policy and procedure documents.",
	glyph: 'RT',
	icon: Search,
	basePath: '/app/retriever',
	status: 'active',
	navItems: [
		{ label: 'Chat', href: '/chat', icon: MessageSquare },
		{ label: 'Documents', href: '/admin', icon: FileText, adminOnly: true }
	]
};
