<script lang="ts">
	import type { ModuleDefinition } from '$lib/portal/types';
	import { Lock } from '@lucide/svelte';
	import ModuleGlyph from './ModuleGlyph.svelte';

	interface Props {
		module: ModuleDefinition;
		active: boolean;
		collapsed: boolean;
		onclick: () => void;
	}

	let { module, active, collapsed, onclick }: Props = $props();

	// Both locked and disabled modules are greyed and non-clickable in the sidebar.
	let isUnavailable = $derived(module.status === 'locked' || module.status === 'disabled');
</script>

<button
	type="button"
	class="module-row flex w-full items-center gap-3 transition-colors"
	class:module-row--active={active}
	class:module-row--unavailable={isUnavailable}
	class:module-row--collapsed={collapsed}
	onclick={onclick}
	disabled={isUnavailable}
	aria-current={active ? 'page' : undefined}
	title={collapsed ? module.name : undefined}
>
	<ModuleGlyph glyph={module.glyph} size={30} radius={7} solid={active} />
	{#if !collapsed}
		<span class="module-row__label truncate">{module.name}</span>
		{#if isUnavailable}
			<Lock size={13} class="ml-auto shrink-0 opacity-40" />
		{/if}
	{/if}
</button>

<style>
	.module-row {
		min-height: 44px;
		padding-inline: 12px;
		border-left: 3px solid transparent;
		color: color-mix(in srgb, var(--portal-sidebar-text) 80%, transparent);
		cursor: pointer;
	}

	.module-row__label {
		font-size: 13.5px;
		font-weight: 500;
	}

	.module-row:hover:not(:disabled) {
		background-color: color-mix(in srgb, var(--portal-sidebar-text) 6%, transparent);
		color: var(--portal-sidebar-text);
	}

	.module-row--active {
		border-left-color: var(--portal-sidebar-accent);
		background-color: color-mix(in srgb, var(--portal-sidebar-accent) 12%, transparent);
		color: var(--portal-sidebar-text);
	}

	.module-row--active .module-row__label {
		font-weight: 600;
	}

	.module-row--unavailable {
		opacity: 0.4;
		cursor: default;
	}

	.module-row--collapsed {
		justify-content: center;
		padding-inline: 0;
		border-left-color: transparent;
	}
</style>
