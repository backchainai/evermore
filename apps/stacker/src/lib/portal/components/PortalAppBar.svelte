<script lang="ts">
	import type { ModuleDefinition } from '$lib/portal/types';
	import { Menu } from '@lucide/svelte';
	import ModuleGlyph from './ModuleGlyph.svelte';
	import ThemePicker from './ThemePicker.svelte';
	import AnimalSubjectSelector from './AnimalSubjectSelector.svelte';

	interface Props {
		activeModule: ModuleDefinition | null;
		session: { access_token?: string } | null;
		petdataApiUrl: string;
		onmenuclick: () => void;
	}

	let { activeModule, session, petdataApiUrl, onmenuclick }: Props = $props();
</script>

<header
	class="flex h-14 shrink-0 items-center border-b border-[var(--portal-border-color)] bg-[var(--portal-card-bg)] px-4"
>
	<!-- Lead: hamburger (mobile) + module mark + name -->
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
				<ModuleGlyph glyph={activeModule.glyph} size={26} radius={6} solid />
				<span
					class="text-base font-semibold"
					style:font-family="'Outfit', system-ui, sans-serif"
				>
					{activeModule.name}
				</span>
			</div>
		{/if}
	</div>

	<!-- Trail: persistent animal subject + theme -->
	<div class="ml-auto flex items-center gap-2">
		<AnimalSubjectSelector {session} {petdataApiUrl} />
		<ThemePicker />
	</div>
</header>
