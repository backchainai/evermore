<script lang="ts">
	import type { ModuleDefinition } from '$lib/portal/types';
	import { Menu } from '@lucide/svelte';
	import ModuleIcon from './ModuleIcon.svelte';
	import ThemePicker from './ThemePicker.svelte';
	import AnimalSubjectSelector from './AnimalSubjectSelector.svelte';

	interface Props {
		activeModule: ModuleDefinition | null;
		session: { access_token?: string } | null;
		petdataApiUrl: string;
		onmenuclick: () => void;
		showAnimalSelector?: boolean;
		showThemeToggle?: boolean;
	}

	let {
		activeModule,
		session,
		petdataApiUrl,
		onmenuclick,
		showAnimalSelector = true,
		showThemeToggle = true
	}: Props = $props();
</script>

<header
	class="flex h-14 shrink-0 items-center border-b border-[var(--portal-border-color)] bg-[var(--portal-card-bg)] px-4"
>
	<!-- Lead: hamburger (mobile) + module mark + name (or "Home" on the portal root) -->
	<div class="flex items-center gap-3">
		<button
			type="button"
			class="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg transition-colors hover:bg-[var(--portal-hover-bg)] md:hidden"
			onclick={onmenuclick}
			aria-label="Toggle navigation"
		>
			<Menu size={20} />
		</button>

		{#if activeModule}
			<div class="flex items-center gap-2.5">
				<ModuleIcon icon={activeModule.icon} svgSize={16} />
				<span
					class="text-base font-semibold"
					style:font-family="'Outfit', system-ui, sans-serif"
				>
					{activeModule.name}
				</span>
			</div>
		{:else}
			<span
				class="text-base font-semibold"
				style:font-family="'Outfit', system-ui, sans-serif"
			>
				Home
			</span>
		{/if}
	</div>

	<!-- Trail: persistent animal subject + theme -->
	<div class="ml-auto flex items-center gap-2">
		{#if showAnimalSelector}
			<AnimalSubjectSelector {session} {petdataApiUrl} />
		{/if}
		{#if showThemeToggle}
			<ThemePicker />
		{/if}
	</div>
</header>
