<script lang="ts">
	import type { ModuleDefinition } from '$lib/portal/types';
	import { Lock } from '@lucide/svelte';

	interface Props {
		module: ModuleDefinition;
		active: boolean;
		collapsed: boolean;
		onclick: () => void;
	}

	let { module, active, collapsed, onclick }: Props = $props();

	let isLocked = $derived(module.status === 'locked');
	let isDisabled = $derived(module.status === 'disabled');
	// Both locked and disabled modules are greyed and non-clickable in the sidebar.
	let isUnavailable = $derived(isLocked || isDisabled);
</script>

<button
	type="button"
	class="module-card group flex w-full items-center gap-3 rounded-lg px-3 transition-colors"
	class:module-card--active={active}
	class:module-card--locked={isUnavailable}
	class:module-card--collapsed={collapsed}
	onclick={onclick}
	disabled={isUnavailable}
	aria-current={active ? 'page' : undefined}
	title={collapsed ? module.name : undefined}
>
	<span class="module-card__icon flex shrink-0 items-center justify-center">
		{#if isUnavailable}
			<Lock size={20} />
		{:else}
			<module.icon size={20} />
		{/if}
	</span>
	{#if !collapsed}
		<span class="module-card__label truncate text-sm font-medium">{module.name}</span>
	{/if}
</button>

<style>
	.module-card {
		min-height: 48px;
		color: var(--portal-sidebar-text);
		cursor: pointer;
		border-left: 3px solid transparent;
	}

	.module-card:hover:not(:disabled) {
		background-color: var(--portal-hover-bg);
		background-color: color-mix(in oklch, var(--portal-sidebar-bg) 70%, white 30%);
	}

	.module-card--active {
		border-left-color: var(--color-primary-500);
		background-color: color-mix(in oklch, var(--portal-sidebar-bg) 60%, white 40%);
	}

	.module-card--locked {
		opacity: 0.4;
		cursor: default;
	}

	.module-card--collapsed {
		justify-content: center;
		padding-inline: 0;
	}
</style>
