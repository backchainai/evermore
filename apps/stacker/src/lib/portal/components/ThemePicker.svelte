<script lang="ts">
	import type { PortalTheme } from '$lib/portal/types';
	import { getTheme, setTheme } from '$lib/portal/theme/theme-store.svelte';
	import { ChevronDown, Check } from '@lucide/svelte';

	let open = $state(false);

	let activeTheme = $derived(getTheme());

	const themes: {
		id: PortalTheme;
		name: string;
		dot: string;
		swatchLeft: string;
		swatchRight: string;
	}[] = [
		{
			id: 'light',
			name: 'Light',
			dot: '#F5F0E8',
			swatchLeft: '#F5F0E8',
			swatchRight: '#A35945'
		},
		{
			id: 'dark',
			name: 'Dark',
			dot: '#2F455B',
			swatchLeft: '#1A2835',
			swatchRight: '#E07A5F'
		},
		{
			id: 'neutral',
			name: 'Neutral',
			dot: '#FAFAF8',
			swatchLeft: '#FAFAF8',
			swatchRight: '#2F455B'
		}
	];

	function selectTheme(id: PortalTheme): void {
		setTheme(id);
		open = false;
	}

	function handleKeydown(event: KeyboardEvent): void {
		if (event.key === 'Escape') {
			open = false;
		}
	}

	function handleClickOutside(event: MouseEvent): void {
		const target = event.target as HTMLElement;
		if (!target.closest('.theme-picker')) {
			open = false;
		}
	}

	$effect(() => {
		if (open) {
			document.addEventListener('click', handleClickOutside, true);
			return () => {
				document.removeEventListener('click', handleClickOutside, true);
			};
		}
	});
</script>

<svelte:window onkeydown={open ? handleKeydown : undefined} />

<div class="theme-picker relative">
	<button
		type="button"
		class="flex min-h-[48px] min-w-[48px] items-center justify-center gap-1.5 rounded-lg px-2 transition-colors hover:bg-[var(--portal-hover-bg)]"
		onclick={() => (open = !open)}
		aria-expanded={open}
		aria-haspopup="listbox"
		aria-label="Choose theme"
	>
		<span
			class="h-4 w-4 rounded-full border border-[var(--portal-border-color)]"
			style:background-color={themes.find((t) => t.id === activeTheme)?.dot ?? '#F5F0E8'}
		></span>
		<ChevronDown size={14} class="opacity-60" />
	</button>

	{#if open}
		<ul
			class="absolute right-0 top-full z-50 mt-2 w-56 overflow-hidden rounded-xl border border-[var(--portal-border-color)] bg-[var(--portal-card-bg)] shadow-lg"
			role="listbox"
			aria-label="Theme options"
		>
			{#each themes as theme (theme.id)}
				<li role="option" aria-selected={theme.id === activeTheme}>
					<button
						type="button"
						class="flex min-h-[48px] w-full items-center gap-3 px-3 py-2 transition-colors hover:bg-[var(--portal-hover-bg)]"
						onclick={() => selectTheme(theme.id)}
					>
						<span
							class="flex h-8 w-8 shrink-0 overflow-hidden rounded-md border border-[var(--portal-border-color)]"
						>
							<span class="h-full w-1/2" style:background-color={theme.swatchLeft}></span>
							<span class="h-full w-1/2" style:background-color={theme.swatchRight}></span>
						</span>
						<span class="text-sm font-medium">{theme.name}</span>
						{#if theme.id === activeTheme}
							<Check size={16} class="ml-auto text-[var(--color-primary-500)]" />
						{/if}
					</button>
				</li>
			{/each}
		</ul>
	{/if}
</div>
