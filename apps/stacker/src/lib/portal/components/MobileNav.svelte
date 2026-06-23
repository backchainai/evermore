<script lang="ts">
	import type { ModuleNavItem } from '$lib/portal/types';

	interface Props {
		navItems: ModuleNavItem[];
		currentPath: string;
		basePath: string;
	}

	let { navItems, currentPath, basePath }: Props = $props();

	function fullHref(item: ModuleNavItem): string {
		return basePath + item.href;
	}

	function isActive(item: ModuleNavItem): boolean {
		return currentPath.startsWith(fullHref(item));
	}
</script>

<nav
	class="mobile-nav fixed inset-x-0 bottom-0 z-40 flex border-t border-[var(--portal-border-color)] bg-[var(--portal-card-bg)] md:hidden"
	aria-label="Module navigation"
>
	{#each navItems as item (item.label)}
		<a
			href={fullHref(item)}
			class="mobile-nav__tab flex flex-1 flex-col items-center justify-center gap-0.5 py-1"
			class:mobile-nav__tab--active={isActive(item)}
			aria-current={isActive(item) ? 'page' : undefined}
		>
			<item.icon size={20} />
			<span class="text-[11px] leading-tight">{item.label}</span>
		</a>
	{/each}
</nav>

<style>
	.mobile-nav {
		padding-bottom: env(safe-area-inset-bottom, 0px);
	}

	.mobile-nav__tab {
		min-height: 48px;
		color: var(--color-surface-500);
		transition: color 0.15s;
	}

	.mobile-nav__tab--active {
		color: var(--color-primary-500);
		border-top: 2px solid var(--color-primary-500);
	}
</style>
