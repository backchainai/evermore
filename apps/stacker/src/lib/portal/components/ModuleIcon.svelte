<script lang="ts">
	/**
	 * Module mark rendered as a bound lucide line icon. Shared across the sidebar
	 * module rows, the top-bar module mark, and the Portal home cards. The slot is
	 * transparent (no fill, no border) — just an icon.
	 *
	 * - `active` (sidebar row selected) — full `--portal-sidebar-text` color.
	 * - idle — a muted mix of `--portal-sidebar-text` (mirrors ModuleGlyph's 72%).
	 */
	import type { Component } from 'svelte';

	interface Props {
		icon: Component;
		/** Square slot size in px. */
		size?: number;
		/** Lucide svg size in px. */
		svgSize?: number;
		active?: boolean;
	}

	let { icon: Icon, size = 26, svgSize, active = false }: Props = $props();

	let resolvedSvgSize = $derived(svgSize ?? Math.round(size * 0.7));
</script>

<span
	class="module-icon"
	class:module-icon--active={active}
	style:width="{size}px"
	style:height="{size}px"
	aria-hidden="true"
>
	<Icon size={resolvedSvgSize} />
</span>

<style>
	.module-icon {
		display: inline-flex;
		flex-shrink: 0;
		align-items: center;
		justify-content: center;
		background-color: transparent;
		/* Idle (muted) — derived from the sidebar text color so it tracks the theme. */
		color: color-mix(in srgb, var(--portal-sidebar-text) 72%, transparent);
	}

	.module-icon--active {
		color: var(--portal-sidebar-text);
	}
</style>
