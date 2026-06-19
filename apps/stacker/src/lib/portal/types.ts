import type { Component } from 'svelte';

export type PortalTheme = 'light' | 'dark' | 'neutral';
export type ModuleStatus = 'active' | 'disabled' | 'locked';

export interface ModuleNavItem {
	label: string;
	href: string;
	icon: Component;
	adminOnly?: boolean;
}

export interface ModuleDefinition {
	id: string;
	name: string;
	description: string;
	icon: Component;
	basePath: string;
	navItems: ModuleNavItem[];
	status: ModuleStatus;
}
