<script lang="ts">
	import { PUBLIC_PETBIO_API_URL } from '$env/static/public';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { PetBioApi } from '$lib/modules/petbio/api/client';
	import type { AnimalDetailResponse } from '$lib/modules/petbio/api/types';
	import ErrorAlert from '$lib/portal/shared/ErrorAlert.svelte';

	let { data } = $props();

	let detail: AnimalDetailResponse | null = $state(null);
	let isLoading = $state(true);
	let error: string | null = $state(null);

	const animalId = $derived($page.params.id ?? '');
	const api = $derived(
		new PetBioApi(
			PUBLIC_PETBIO_API_URL || 'http://localhost:8002',
			data.session?.access_token ?? ''
		)
	);

	onMount(() => {
		if (data.session && animalId) {
			loadAnimal();
		}
	});

	async function loadAnimal() {
		isLoading = true;
		try {
			detail = await api.getAnimal(animalId);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load animal.';
		} finally {
			isLoading = false;
		}
	}

	function formatDate(iso: string | null): string {
		if (!iso) return '—';
		try {
			return new Date(iso).toLocaleDateString();
		} catch {
			return iso;
		}
	}

	function ratingBar(value: number | null, max: number = 5): string {
		if (value == null) return '—';
		return '●'.repeat(value) + '○'.repeat(max - value);
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
	<title>{detail?.animal.name ?? 'Animal'} – PetBio</title>
</svelte:head>

<div class="mx-auto max-w-4xl p-4">
	{#if error}
		<div class="mb-4">
			<ErrorAlert message={error} ondismiss={() => (error = null)} />
		</div>
	{/if}

	{#if isLoading}
		<p class="animate-pulse text-surface-400">Loading animal...</p>
	{:else if detail}
		{@const a = detail.animal}

		<!-- Header -->
		<div class="mb-6 flex items-start justify-between">
			<div>
				<a href="/app/petbio/animals" class="text-sm text-surface-400 hover:underline">← Animals</a>
				<h1 class="mt-1 text-2xl font-bold">{a.name}</h1>
				{#if a.aka}
					<p class="text-sm text-surface-400">aka {a.aka}</p>
				{/if}
			</div>
			{#if a.color_category}
				<span class="rounded-full px-3 py-1 text-sm font-medium {getBadgeClass(a.color_category)}">
					{a.color_category}
				</span>
			{/if}
		</div>

		<!-- Quick facts -->
		<div class="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
			<div class="preset-filled-surface-200-800 rounded-lg p-3">
				<p class="text-xs text-surface-400">Breed</p>
				<p class="font-medium">{a.breed ?? '—'}</p>
			</div>
			<div class="preset-filled-surface-200-800 rounded-lg p-3">
				<p class="text-xs text-surface-400">Age</p>
				<p class="font-medium">{a.age_years != null ? `${a.age_years} yrs` : '—'}</p>
			</div>
			<div class="preset-filled-surface-200-800 rounded-lg p-3">
				<p class="text-xs text-surface-400">Weight</p>
				<p class="font-medium">{a.weight_lbs != null ? `${a.weight_lbs} lbs` : '—'}</p>
			</div>
			<div class="preset-filled-surface-200-800 rounded-lg p-3">
				<p class="text-xs text-surface-400">Days in shelter</p>
				<p class="font-medium">{a.days_in_shelter ?? '—'}</p>
			</div>
		</div>

		<!-- Kennel Card -->
		{#if detail.kennel_card}
			{@const kc = detail.kennel_card}
			<section class="mb-6">
				<h2 class="mb-3 text-lg font-semibold">Kennel Card</h2>
				<div class="preset-filled-surface-200-800 space-y-3 rounded-lg p-4">
					{#if kc.about_text}
						<div>
							<p class="text-xs font-medium text-surface-400">About</p>
							<p class="text-sm">{kc.about_text}</p>
						</div>
					{/if}
					<div class="grid gap-3 sm:grid-cols-3">
						<div>
							<p class="text-xs font-medium text-surface-400">Dogs</p>
							<p class="text-sm">{kc.dogs_compatibility ?? '—'}</p>
						</div>
						<div>
							<p class="text-xs font-medium text-surface-400">Cats</p>
							<p class="text-sm">{kc.cats_compatibility ?? '—'}</p>
						</div>
						<div>
							<p class="text-xs font-medium text-surface-400">Kids</p>
							<p class="text-sm">{kc.kids_compatibility ?? '—'}</p>
						</div>
					</div>
					{#if kc.things_likes || kc.things_dislikes}
						<div class="grid gap-3 sm:grid-cols-2">
							{#if kc.things_likes}
								<div>
									<p class="text-xs font-medium text-surface-400">Likes</p>
									<p class="text-sm">{kc.things_likes}</p>
								</div>
							{/if}
							{#if kc.things_dislikes}
								<div>
									<p class="text-xs font-medium text-surface-400">Dislikes</p>
									<p class="text-sm">{kc.things_dislikes}</p>
								</div>
							{/if}
						</div>
					{/if}
				</div>
			</section>
		{/if}

		<!-- Volunteer Notes -->
		<section class="mb-6">
			<h2 class="mb-3 text-lg font-semibold">
				Volunteer Notes ({detail.volunteer_notes.length})
			</h2>
			{#if detail.volunteer_notes.length === 0}
				<p class="text-sm text-surface-400">No volunteer notes recorded.</p>
			{:else}
				<div class="space-y-3">
					{#each detail.volunteer_notes as note}
						<div class="preset-filled-surface-200-800 rounded-lg p-4">
							<div class="mb-2 flex items-center justify-between text-xs text-surface-400">
								<span>{note.volunteer_name}</span>
								<span>{formatDate(note.note_date)}</span>
							</div>
							{#if note.note_text}
								<p class="mb-2 text-sm">{note.note_text}</p>
							{/if}
							<div class="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
								<div>
									<span class="text-surface-400">Leash strength</span>
									<span class="ml-1">{ratingBar(note.rating_strong_on_leash)}</span>
								</div>
								<div>
									<span class="text-surface-400">Reactivity</span>
									<span class="ml-1">{ratingBar(note.rating_leash_reactivity)}</span>
								</div>
								<div>
									<span class="text-surface-400">Shy/Fearful</span>
									<span class="ml-1">{ratingBar(note.rating_shy_fearful)}</span>
								</div>
								<div>
									<span class="text-surface-400">Jumpy/Mouthy</span>
									<span class="ml-1">{ratingBar(note.rating_jumpy_mouthy)}</span>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</section>

		<!-- Staff Assessments -->
		{#if detail.staff_assessments.length > 0}
			<section class="mb-6">
				<h2 class="mb-3 text-lg font-semibold">
					Staff Assessments ({detail.staff_assessments.length})
				</h2>
				<div class="space-y-3">
					{#each detail.staff_assessments as assessment}
						<div class="preset-filled-surface-200-800 rounded-lg p-4">
							{#if assessment.recorded_at}
								<p class="mb-2 text-xs text-surface-400">
									{formatDate(assessment.recorded_at)}
								</p>
							{/if}
							{#if assessment.notes}
								<p class="mb-2 text-sm">{assessment.notes}</p>
							{/if}
							{#if assessment.assessment_tags?.length}
								<div class="flex flex-wrap gap-1">
									{#each assessment.assessment_tags as tag}
										<span class="rounded-full bg-surface-500/20 px-2 py-0.5 text-xs">
											{tag}
										</span>
									{/each}
								</div>
							{/if}
						</div>
					{/each}
				</div>
			</section>
		{/if}

		<!-- Behavior tags -->
		{#if a.behavior_mod_tags?.length}
			<section class="mb-6">
				<h2 class="mb-3 text-lg font-semibold">Behavior Tags</h2>
				<div class="flex flex-wrap gap-2">
					{#each a.behavior_mod_tags as tag}
						<span class="rounded-full bg-primary-500/20 px-3 py-1 text-sm text-primary-400">
							{tag}
						</span>
					{/each}
				</div>
			</section>
		{/if}
	{/if}
</div>
