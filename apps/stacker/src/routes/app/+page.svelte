<script lang="ts">
	import { getModulesWithStatus } from '$lib/portal/config';
	import { Lock } from '@lucide/svelte';

	let { data } = $props();

	const subscriptions = $derived(new Set(data.subscriptions || []));
	const modules = $derived(getModulesWithStatus(subscriptions));
</script>

<svelte:head>
	<title>Portal</title>
</svelte:head>

<div class="mx-auto max-w-4xl p-6">
	<h1
		class="mb-2 text-2xl font-bold"
		style:font-family="'Outfit', system-ui, sans-serif"
	>
		Welcome back
	</h1>
	<p class="mb-8 text-sm opacity-60">Select a module to get started.</p>

	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
		{#each modules as mod}
			{@const isActive = mod.status === 'active'}
			{@const statusLabel = mod.status === 'disabled' ? 'In development' : 'Coming Soon'}
			{@const href = isActive && mod.navItems.length > 0
				? mod.basePath + mod.navItems[0].href
				: isActive
					? mod.basePath
					: undefined}

			{#if isActive && href}
				<a
					{href}
					class="group flex flex-col gap-3 rounded-xl border border-[var(--portal-border-color)] bg-[var(--portal-card-bg)] p-5 transition-shadow hover:shadow-lg"
				>
					<span
						class="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--color-primary-500)]/10"
					>
						<mod.icon size={24} class="text-[var(--color-primary-500)]" />
					</span>
					<h2
						class="text-lg font-semibold"
						style:font-family="'Outfit', system-ui, sans-serif"
					>
						{mod.name}
					</h2>
					<p class="text-sm opacity-60">{mod.description}</p>
				</a>
			{:else}
				<div
					class="flex flex-col gap-3 rounded-xl border border-[var(--portal-border-color)] bg-[var(--portal-card-bg)] p-5 opacity-50"
				>
					<span
						class="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--portal-border-color)]/20"
					>
						<Lock size={24} class="opacity-40" />
					</span>
					<h2
						class="text-lg font-semibold"
						style:font-family="'Outfit', system-ui, sans-serif"
					>
						{mod.name}
					</h2>
					<p class="text-sm opacity-60">{mod.description}</p>
					<span class="mt-auto text-xs font-medium uppercase tracking-wide opacity-40">
						{statusLabel}
					</span>
				</div>
			{/if}
		{/each}
	</div>
</div>
