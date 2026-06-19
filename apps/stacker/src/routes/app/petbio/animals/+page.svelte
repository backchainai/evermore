<script lang="ts">
	import { PUBLIC_PETBIO_API_URL } from '$env/static/public';
	import { onMount } from 'svelte';
	import { PetBioApi } from '$lib/modules/petbio/api/client';
	import type { Animal } from '$lib/modules/petbio/api/types';
	import ErrorAlert from '$lib/portal/shared/ErrorAlert.svelte';

	let { data } = $props();

	let animals: Animal[] = $state([]);
	let isLoading = $state(true);
	let error: string | null = $state(null);

	const api = $derived(
		new PetBioApi(
			PUBLIC_PETBIO_API_URL || 'http://localhost:8002',
			data.session?.access_token ?? ''
		)
	);

	onMount(() => {
		if (data.session) {
			loadAnimals();
		}
	});

	async function loadAnimals() {
		isLoading = true;
		try {
			const result = await api.listAnimals();
			animals = result.animals;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load animals.';
		} finally {
			isLoading = false;
		}
	}

	function getBadgeClass(category: string | null): string {
		switch (category?.toLowerCase()) {
			case 'green':
				return 'bg-success-500/20 text-success-400';
			case 'yellow':
				return 'bg-warning-500/20 text-warning-400';
			case 'orange':
				return 'bg-error-500/20 text-error-400';
			default:
				return 'bg-surface-500/20 text-surface-400';
		}
	}
</script>

<svelte:head>
	<title>Animals – PetBio</title>
</svelte:head>

<div class="mx-auto max-w-4xl p-4">
	<h1 class="mb-6 text-2xl font-bold">Animals</h1>

	{#if error}
		<div class="mb-4">
			<ErrorAlert message={error} ondismiss={() => (error = null)} />
		</div>
	{/if}

	{#if isLoading}
		<p class="animate-pulse text-surface-400">Loading animals...</p>
	{:else if animals.length === 0}
		<div class="mt-10 text-center text-surface-500">
			<p class="text-lg font-medium">No animals found</p>
			<p class="mt-1 text-sm">Sync data from FOHA to see animals here.</p>
		</div>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each animals as animal}
				<a
					href="/app/petbio/animals/{animal.id}"
					class="preset-filled-surface-200-800 block rounded-lg p-4 transition-shadow hover:shadow-md"
				>
					<div class="flex items-start justify-between">
						<h3 class="font-semibold">{animal.name}</h3>
						{#if animal.color_category}
							<span class="rounded-full px-2 py-0.5 text-xs {getBadgeClass(animal.color_category)}">
								{animal.color_category}
							</span>
						{/if}
					</div>
					{#if animal.breed}
						<p class="mt-1 text-sm text-surface-400">{animal.breed}</p>
					{/if}
					<div class="mt-2 flex gap-3 text-xs text-surface-500">
						{#if animal.age_years != null}
							<span>{animal.age_years} yrs</span>
						{/if}
						{#if animal.days_in_shelter != null}
							<span>{animal.days_in_shelter}d in shelter</span>
						{/if}
						{#if animal.location}
							<span>{animal.location}</span>
						{/if}
					</div>
				</a>
			{/each}
		</div>
	{/if}
</div>
