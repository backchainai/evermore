<script lang="ts">
	import { getModulesWithStatus } from '$lib/portal/config';
	import ModuleGlyph from '$lib/portal/components/ModuleGlyph.svelte';
	import { firstNameFromEmail } from '$lib/portal/user-display';

	let { data } = $props();

	const subscriptions = $derived(new Set(data.subscriptions || []));
	// Only active modules are surfaced as live cards here; locked/disabled modules
	// are reached (and gated) through the sidebar, not linked from the home grid.
	const availableModules = $derived(
		getModulesWithStatus(subscriptions).filter((m) => m.status === 'active')
	);

	const firstName = $derived(firstNameFromEmail(data.user?.email));

	function moduleHref(mod: (typeof availableModules)[number]): string {
		return mod.navItems.length > 0 ? mod.basePath + mod.navItems[0].href : mod.basePath;
	}
</script>

<svelte:head>
	<title>Evermore</title>
</svelte:head>

<div class="home mx-auto">
	<span class="eyebrow">Signed in</span>
	<h1 class="welcome">Welcome back, {firstName}</h1>
	<p class="subhead">Pick a module to get started.</p>

	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
		{#each availableModules as mod (mod.id)}
			<a href={moduleHref(mod)} class="module-card flex flex-col">
				<ModuleGlyph glyph={mod.glyph} size={46} radius={10} solid />
				<h2 class="card-title">{mod.name}</h2>
				<p class="card-desc">{mod.description}</p>
				<span class="card-open">Open →</span>
			</a>
		{/each}
	</div>
</div>

<style>
	.home {
		max-width: 940px;
		padding: 48px;
	}

	.eyebrow {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--color-primary-500);
	}

	.welcome {
		margin-top: 0.5rem;
		font-family: 'Outfit', system-ui, sans-serif;
		font-size: 30px;
		font-weight: 600;
		letter-spacing: -0.01em;
	}

	.subhead {
		margin-top: 0.375rem;
		margin-bottom: 2rem;
		font-size: 14px;
		opacity: 0.6;
	}

	.module-card {
		gap: 0.75rem;
		padding: 22px;
		border: 1px solid var(--portal-border-color);
		border-radius: 8px;
		background-color: var(--portal-card-bg);
		text-decoration: none;
		transition:
			transform 0.2s ease,
			border-color 0.2s ease,
			box-shadow 0.2s ease;
	}

	.module-card:hover {
		transform: translateY(-2px);
		/* Darken the hairline by mixing toward the dark sidebar slate; stays token-driven. */
		border-color: color-mix(in srgb, var(--portal-border-color) 55%, var(--portal-sidebar-bg) 45%);
		box-shadow: 0 8px 24px -12px color-mix(in srgb, var(--portal-sidebar-bg) 28%, transparent);
		text-decoration: none;
	}

	.card-title {
		font-family: 'Outfit', system-ui, sans-serif;
		font-size: 18px;
		font-weight: 600;
	}

	.card-desc {
		font-size: 13px;
		opacity: 0.6;
	}

	.card-open {
		margin-top: auto;
		font-size: 12.5px;
		font-weight: 600;
		color: var(--color-primary-500);
	}
</style>
