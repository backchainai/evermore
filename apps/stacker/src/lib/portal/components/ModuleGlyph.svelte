<script lang="ts">
	/**
	 * Two-letter module glyph tile (e.g. "RT", "PD"). Shared across the sidebar
	 * module rows, the top-bar module mark, and the Portal home cards.
	 *
	 * - `solid` (blue fill, white text) — active sidebar row, top bar, cards.
	 * - default (muted) — idle sidebar rows, derived from the sidebar text color.
	 */
	interface Props {
		glyph: string;
		size?: number;
		radius?: number;
		solid?: boolean;
	}

	let { glyph, size = 30, radius = 7, solid = false }: Props = $props();
</script>

<span
	class="module-glyph"
	class:module-glyph--solid={solid}
	style:width="{size}px"
	style:height="{size}px"
	style:border-radius="{radius}px"
	style:font-size="{Math.round(size * 0.4)}px"
	aria-hidden="true"
>
	{glyph}
</span>

<style>
	.module-glyph {
		display: inline-flex;
		flex-shrink: 0;
		align-items: center;
		justify-content: center;
		font-family: 'Outfit', system-ui, sans-serif;
		font-weight: 700;
		line-height: 1;
		letter-spacing: 0.01em;
		/* Idle (muted) — derived from the sidebar text color so it tracks the theme. */
		background-color: color-mix(in srgb, var(--portal-sidebar-text) 12%, transparent);
		color: color-mix(in srgb, var(--portal-sidebar-text) 72%, transparent);
	}

	.module-glyph--solid {
		background-color: var(--color-primary-500);
		color: #fff;
	}
</style>
