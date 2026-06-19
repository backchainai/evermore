<script lang="ts">
	import type { ModuleDefinition } from '$lib/portal/types';
	import { Globe, PanelLeftClose, PanelLeftOpen } from '@lucide/svelte';
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

	let { modules, activeModuleId, user, collapsed, onmoduleclick, onlockedclick }: Props =
		$props();

	let internalCollapsed = $state(false);

	// Sync internal state when prop changes
	$effect(() => {
		internalCollapsed = collapsed;
	});

	let isCollapsed = $derived(internalCollapsed);

	let activeModule = $derived(modules.find((m) => m.id === activeModuleId) ?? null);

	function handleModuleClick(mod: ModuleDefinition): void {
		if (mod.status === 'locked') {
			onlockedclick(mod);
		} else {
			onmoduleclick(mod);
		}
	}

	function toggleCollapse(): void {
		internalCollapsed = !internalCollapsed;
	}
</script>

<aside
	class="portal-sidebar flex h-full flex-col overflow-y-auto"
	class:portal-sidebar--collapsed={isCollapsed}
>
	<!-- Header: wordmark + collapse toggle -->
	<div class="flex min-h-[56px] shrink-0 items-center gap-2 border-b border-white/10 px-4">
		<Globe size={22} class="shrink-0 text-[var(--portal-sidebar-accent)]" />
		{#if !isCollapsed}
			<span
				class="text-base font-semibold tracking-tight text-[var(--portal-sidebar-text)]"
				style:font-family="'Outfit', system-ui, sans-serif"
			>
				Portal
			</span>
			<button
				type="button"
				class="ml-auto flex min-h-[48px] min-w-[48px] items-center justify-center rounded-lg text-[var(--portal-sidebar-text)] opacity-60 transition-opacity hover:opacity-100"
				onclick={toggleCollapse}
				aria-label="Collapse sidebar"
			>
				<PanelLeftClose size={18} />
			</button>
		{:else}
			<button
				type="button"
				class="ml-auto flex min-h-[48px] min-w-[48px] items-center justify-center rounded-lg text-[var(--portal-sidebar-text)] opacity-60 transition-opacity hover:opacity-100"
				onclick={toggleCollapse}
				aria-label="Expand sidebar"
			>
				<PanelLeftOpen size={18} />
			</button>
		{/if}
	</div>

	<!-- Module list -->
	<nav class="flex flex-1 flex-col gap-1 px-2 pt-4" aria-label="Modules">
		{#if !isCollapsed}
			<span class="mb-1 px-3 text-[11px] font-semibold uppercase tracking-wider text-[var(--portal-sidebar-text)] opacity-50">
				Modules
			</span>
		{/if}

		{#each modules as mod (mod.id)}
			<ModuleCard
				module={mod}
				active={mod.id === activeModuleId}
				collapsed={isCollapsed}
				onclick={() => handleModuleClick(mod)}
			/>
		{/each}

		<!-- Active module nav items -->
		{#if activeModule && activeModule.navItems.length > 0}
			<div class="mt-4 border-t border-white/10 pt-4">
				{#if !isCollapsed}
					<span class="mb-1 px-3 text-[11px] font-semibold uppercase tracking-wider text-[var(--portal-sidebar-text)] opacity-50">
						{activeModule.name}
					</span>
				{/if}
				{#each activeModule.navItems as navItem (navItem.label)}
					<a
						href={activeModule.basePath + navItem.href}
						class="nav-link flex items-center gap-3 rounded-lg px-3 text-sm text-[var(--portal-sidebar-text)] transition-colors hover:bg-[color-mix(in_oklch,var(--portal-sidebar-bg)_70%,white_30%)]"
						class:nav-link--collapsed={isCollapsed}
						title={isCollapsed ? navItem.label : undefined}
					>
						<navItem.icon size={18} class="shrink-0" />
						{#if !isCollapsed}
							<span class="truncate">{navItem.label}</span>
						{/if}
					</a>
				{/each}
			</div>
		{/if}
	</nav>

	<!-- Footer: user menu -->
	<div class="mt-auto shrink-0 border-t border-white/10 p-2">
		<UserMenu {user} compact={isCollapsed} />
	</div>
</aside>

<style>
	.portal-sidebar {
		background-color: var(--portal-sidebar-bg);
		width: 260px;
		transition: width 0.2s ease;
	}

	.portal-sidebar--collapsed {
		width: 72px;
	}

	.nav-link {
		min-height: 48px;
	}

	.nav-link--collapsed {
		justify-content: center;
		padding-inline: 0;
	}
</style>
