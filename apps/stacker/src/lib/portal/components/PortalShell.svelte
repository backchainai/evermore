<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { ModuleDefinition, ModuleNavItem } from '$lib/portal/types';
	import PortalAppBar from './PortalAppBar.svelte';
	import PortalSidebar from './PortalSidebar.svelte';
	import MobileNav from './MobileNav.svelte';
	import SubscriptionGate from './SubscriptionGate.svelte';

	interface Props {
		modules: ModuleDefinition[];
		activeModuleId: string | null;
		user: { email: string; role?: string } | null;
		children: Snippet;
	}

	let { modules, activeModuleId, user, children }: Props = $props();

	let mobileMenuOpen = $state(false);
	let gatedModule: ModuleDefinition | null = $state(null);

	let activeModule = $derived(modules.find((m) => m.id === activeModuleId) ?? null);
	let activeNavItems: ModuleNavItem[] = $derived(activeModule?.navItems ?? []);
	let activeBasePath = $derived(activeModule?.basePath ?? '');

	let currentPath = $state('');

	$effect(() => {
		if (typeof window !== 'undefined') {
			currentPath = window.location.pathname;
		}
	});

	function handleModuleClick(mod: ModuleDefinition): void {
		if (mod.navItems.length > 0) {
			window.location.href = mod.basePath + mod.navItems[0].href;
		} else {
			window.location.href = mod.basePath;
		}
	}

	function handleLockedClick(mod: ModuleDefinition): void {
		gatedModule = mod;
	}

	function closeMobileMenu(): void {
		mobileMenuOpen = !mobileMenuOpen;
	}
</script>

<div class="portal-shell grid h-dvh">
	<!-- Sidebar: hidden on mobile, rail on tablet, full on desktop -->
	<aside class="portal-shell__sidebar hidden overflow-hidden md:block" aria-label="Sidebar">
		<PortalSidebar
			{modules}
			{activeModuleId}
			{user}
			collapsed={false}
			onmoduleclick={handleModuleClick}
			onlockedclick={handleLockedClick}
		/>
	</aside>

	<!-- Main column -->
	<div class="flex min-h-0 min-w-0 flex-col">
		<PortalAppBar
			{activeModule}
			{user}
			onmenuclick={closeMobileMenu}
		/>

		<!-- Content area -->
		<main id="main" class="flex-1 overflow-y-auto">
			{@render children()}
		</main>
	</div>

	<!-- Mobile bottom nav (below md) -->
	{#if activeNavItems.length > 0}
		<MobileNav navItems={activeNavItems} {currentPath} basePath={activeBasePath} />
	{/if}

	<!-- Mobile sidebar overlay -->
	{#if mobileMenuOpen}
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			class="fixed inset-0 z-40 flex md:hidden"
			onclick={closeMobileMenu}
		>
			<div class="absolute inset-0 bg-black/40" aria-hidden="true"></div>
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="relative z-10 h-full" onclick={(e) => e.stopPropagation()}>
				<PortalSidebar
					{modules}
					{activeModuleId}
					{user}
					collapsed={false}
					onmoduleclick={(mod) => { handleModuleClick(mod); mobileMenuOpen = false; }}
					onlockedclick={(mod) => { handleLockedClick(mod); mobileMenuOpen = false; }}
				/>
			</div>
		</div>
	{/if}

	<!-- Subscription gate modal -->
	{#if gatedModule}
		<SubscriptionGate
			module={gatedModule}
			onclose={() => (gatedModule = null)}
		/>
	{/if}
</div>

<style>
	.portal-shell {
		grid-template-columns: 1fr;
		grid-template-rows: 1fr;
	}

	/* Tablet: rail sidebar */
	@media (min-width: 768px) {
		.portal-shell {
			grid-template-columns: 72px 1fr;
		}
	}

	/* Desktop: full sidebar */
	@media (min-width: 1024px) {
		.portal-shell {
			grid-template-columns: 260px 1fr;
		}
	}
</style>
