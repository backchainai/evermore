<script lang="ts">
	import type { ModuleDefinition } from '$lib/portal/types';
	import { page } from '$app/stores';
	import ModuleCard from './ModuleCard.svelte';
	import UserMenu from './UserMenu.svelte';

	interface Props {
		modules: ModuleDefinition[];
		activeModuleId: string | null;
		user: { email: string; role?: string } | null;
		collapsed: boolean;
		onmoduleclick: (module: ModuleDefinition) => void;
		onlockedclick: (module: ModuleDefinition) => void;
	}

	let { modules, activeModuleId, user, collapsed, onmoduleclick, onlockedclick }: Props = $props();

	let isCollapsed = $derived(collapsed);
	let activeModule = $derived(modules.find((m) => m.id === activeModuleId) ?? null);
	let currentPath = $derived($page.url.pathname);

	function handleModuleClick(mod: ModuleDefinition): void {
		if (mod.status === 'disabled') {
			return; // in-development modules are inert (the card is also disabled)
		}
		if (mod.status === 'locked') {
			onlockedclick(mod);
		} else {
			onmoduleclick(mod);
		}
	}

	function isNavActive(href: string): boolean {
		return currentPath === href || currentPath.startsWith(href + '/');
	}
</script>

<aside class="portal-sidebar flex h-full flex-col overflow-y-auto">
	<!-- Header: blue dot + wordmark, links home -->
	<a
		href="/app"
		class="header flex min-h-[56px] shrink-0 items-center gap-2.5 border-b border-white/[0.08] px-4"
	>
		<span class="dot" aria-hidden="true"></span>
		{#if !isCollapsed}
			<span class="wordmark">Evermore</span>
		{/if}
	</a>

	<!-- Module list -->
	<nav class="flex flex-1 flex-col gap-1 px-2 pt-4" aria-label="Modules">
		{#if !isCollapsed}
			<span class="eyebrow px-3">Modules</span>
		{/if}

		{#each modules as mod (mod.id)}
			<ModuleCard
				module={mod}
				active={mod.id === activeModuleId}
				collapsed={isCollapsed}
				onclick={() => handleModuleClick(mod)}
			/>
		{/each}

		<!-- Active module sub-nav -->
		{#if activeModule && activeModule.navItems.length > 0}
			<div class="mt-4 border-t border-white/[0.08] pt-4">
				{#if !isCollapsed}
					<span class="eyebrow px-3">{activeModule.name}</span>
				{/if}
				{#each activeModule.navItems as navItem (navItem.label)}
					{@const href = activeModule.basePath + navItem.href}
					<a
						{href}
						class="sub-nav flex items-center gap-2.5"
						class:sub-nav--active={isNavActive(href)}
						class:sub-nav--collapsed={isCollapsed}
						aria-current={isNavActive(href) ? 'page' : undefined}
						title={isCollapsed ? navItem.label : undefined}
					>
						<span class="marker" aria-hidden="true"></span>
						{#if !isCollapsed}
							<span class="truncate">{navItem.label}</span>
						{/if}
					</a>
				{/each}
			</div>
		{/if}
	</nav>

	<!-- Footer: account menu -->
	<div class="mt-auto shrink-0 border-t border-white/[0.08] p-2">
		<UserMenu {user} />
	</div>
</aside>

<style>
	.portal-sidebar {
		background-color: var(--portal-sidebar-bg);
		width: 260px;
	}

	.header {
		text-decoration: none;
	}

	.header:hover {
		text-decoration: none;
	}

	.dot {
		height: 8px;
		width: 8px;
		flex-shrink: 0;
		border-radius: 9999px;
		background-color: var(--portal-sidebar-accent);
	}

	.wordmark {
		font-family: 'Outfit', system-ui, sans-serif;
		font-size: 16px;
		font-weight: 600;
		letter-spacing: -0.01em;
		color: var(--portal-sidebar-text);
	}

	.eyebrow {
		margin-bottom: 0.25rem;
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: color-mix(in srgb, var(--portal-sidebar-text) 50%, transparent);
	}

	.sub-nav {
		min-height: 38px;
		padding-inline: 12px;
		border-radius: 8px;
		font-size: 13px;
		color: color-mix(in srgb, var(--portal-sidebar-text) 72%, transparent);
		transition: background-color 0.2s ease, color 0.2s ease;
	}

	.sub-nav:hover {
		background-color: color-mix(in srgb, var(--portal-sidebar-text) 6%, transparent);
		color: var(--portal-sidebar-text);
		text-decoration: none;
	}

	.sub-nav--active {
		background-color: rgba(255, 255, 255, 0.08);
		color: var(--portal-sidebar-text);
		font-weight: 500;
	}

	.marker {
		height: 6px;
		width: 6px;
		flex-shrink: 0;
		border-radius: 9999px;
		background-color: currentColor;
		opacity: 0.55;
	}

	.sub-nav--active .marker {
		opacity: 1;
		background-color: var(--portal-sidebar-accent);
	}

	.sub-nav--collapsed {
		justify-content: center;
		padding-inline: 0;
	}
</style>
