<script lang="ts">
	/**
	 * Animal-subject selector — global chrome present on every module. A pill
	 * showing the persistent animal that follows the user across modules; opening
	 * it lists animals from Pet Data so the user can switch subjects. Selection is
	 * held in the shared animal-subject store (mirrored to localStorage).
	 */
	import { onMount } from 'svelte';
	import { ChevronDown, Check, X } from '@lucide/svelte';
	import { PetDataApi } from '$lib/modules/petdata/api/client';
	import type { Animal } from '$lib/modules/petdata/api/types';
	import {
		getAnimalSubject,
		setAnimalSubject,
		initAnimalSubject
	} from '$lib/portal/state/animal-subject.svelte';

	interface Props {
		session: { access_token?: string } | null;
		petdataApiUrl: string;
	}

	let { session, petdataApiUrl }: Props = $props();

	let open = $state(false);
	let animals = $state<Animal[]>([]);
	let loaded = $state(false);
	let isLoading = $state(false);
	let loadError = $state<string | null>(null);

	const subject = $derived(getAnimalSubject());
	const api = $derived(
		new PetDataApi(petdataApiUrl || 'http://localhost:8002', session?.access_token ?? '')
	);

	onMount(() => {
		initAnimalSubject();
	});

	async function loadAnimals(): Promise<void> {
		if (loaded || isLoading) return;
		if (!session?.access_token) {
			loadError = 'Sign in to choose an animal.';
			return;
		}
		isLoading = true;
		loadError = null;
		try {
			const result = await api.listAnimals();
			animals = result.animals;
			loaded = true;
		} catch (err) {
			loadError = err instanceof Error ? err.message : 'Could not load animals.';
		} finally {
			isLoading = false;
		}
	}

	function toggle(): void {
		open = !open;
		if (open) void loadAnimals();
	}

	function select(animal: Animal): void {
		setAnimalSubject({ id: animal.id, name: animal.name });
		open = false;
	}

	function clearSubject(): void {
		setAnimalSubject(null);
		open = false;
	}

	function initialOf(name: string | null | undefined): string {
		return name?.trim()?.charAt(0)?.toUpperCase() || '?';
	}

	function handleClickOutside(event: MouseEvent): void {
		const target = event.target as HTMLElement;
		if (!target.closest('.animal-subject')) open = false;
	}

	function handleKeydown(event: KeyboardEvent): void {
		if (event.key === 'Escape') open = false;
	}

	$effect(() => {
		if (open) {
			document.addEventListener('click', handleClickOutside, true);
			return () => document.removeEventListener('click', handleClickOutside, true);
		}
	});
</script>

<svelte:window onkeydown={open ? handleKeydown : undefined} />

<div class="animal-subject relative">
	<button
		type="button"
		class="pill flex items-center gap-2"
		onclick={toggle}
		aria-haspopup="listbox"
		aria-expanded={open}
		aria-label="Animal subject"
	>
		<span class="avatar" aria-hidden="true">{initialOf(subject?.name)}</span>
		<span class="flex min-w-0 flex-col items-start leading-tight">
			<span class="eyebrow">Animal</span>
			<span class="name truncate">{subject?.name ?? 'Select animal'}</span>
		</span>
		<ChevronDown size={14} class="shrink-0 opacity-50" />
	</button>

	{#if open}
		<div
			class="menu absolute right-0 top-full z-50 mt-2 w-72 overflow-hidden rounded-xl border border-[var(--portal-border-color)] bg-[var(--portal-card-bg)] shadow-lg"
			role="listbox"
			aria-label="Choose an animal"
		>
			{#if isLoading}
				<p class="px-4 py-3 text-sm opacity-60">Loading animals…</p>
			{:else if loadError}
				<p class="px-4 py-3 text-sm text-[var(--color-error-500)]">{loadError}</p>
			{:else if animals.length === 0}
				<p class="px-4 py-3 text-sm opacity-60">No animals available yet.</p>
			{:else}
				<ul class="max-h-80 overflow-y-auto py-1">
					{#each animals as animal (animal.id)}
						{@const isSelected = subject?.id === animal.id}
						<li role="option" aria-selected={isSelected}>
							<button
								type="button"
								class="row flex w-full items-center gap-3 px-3 py-2 text-left transition-colors hover:bg-[var(--portal-hover-bg)]"
								onclick={() => select(animal)}
							>
								<span class="avatar avatar--sm" aria-hidden="true">{initialOf(animal.name)}</span>
								<span class="flex min-w-0 flex-col">
									<span class="truncate text-sm font-medium">{animal.name}</span>
									{#if animal.breed}
										<span class="truncate text-xs opacity-55">{animal.breed}</span>
									{/if}
								</span>
								{#if isSelected}
									<Check size={16} class="ml-auto shrink-0 text-[var(--color-primary-500)]" />
								{/if}
							</button>
						</li>
					{/each}
				</ul>
			{/if}

			{#if subject}
				<div class="border-t border-[var(--portal-border-color)]">
					<button
						type="button"
						class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm opacity-70 transition-colors hover:bg-[var(--portal-hover-bg)]"
						onclick={clearSubject}
					>
						<X size={14} class="shrink-0" />
						Clear selection
					</button>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.pill {
		min-height: 40px;
		padding: 0.25rem 0.625rem 0.25rem 0.3rem;
		border: 1px solid var(--portal-border-color);
		border-radius: 9999px;
		background-color: var(--portal-card-bg);
		transition:
			border-color 0.2s ease,
			transform 0.2s ease;
	}

	.pill:hover {
		border-color: color-mix(in srgb, var(--color-primary-500) 45%, var(--portal-border-color));
	}

	.pill:active {
		transform: scale(0.98);
	}

	.avatar {
		display: inline-flex;
		height: 28px;
		width: 28px;
		flex-shrink: 0;
		align-items: center;
		justify-content: center;
		border-radius: 9999px;
		background-color: var(--color-primary-50);
		color: var(--color-primary-500);
		font-size: 12px;
		font-weight: 600;
	}

	.avatar--sm {
		height: 26px;
		width: 26px;
		font-size: 11px;
	}

	.eyebrow {
		font-size: 9px;
		font-weight: 700;
		letter-spacing: 0.09em;
		text-transform: uppercase;
		opacity: 0.5;
	}

	.name {
		max-width: 9rem;
		font-size: 13px;
		font-weight: 600;
	}
</style>
