<script lang="ts">
	import type { ModuleDefinition } from '$lib/portal/types';
	import { Menu } from '@lucide/svelte';
	import ThemePicker from './ThemePicker.svelte';
	import UserMenu from './UserMenu.svelte';

	interface Props {
		activeModule: ModuleDefinition | null;
		user: { email: string; role?: string } | null;
		onmenuclick: () => void;
	}

	let { activeModule, user, onmenuclick }: Props = $props();
</script>

<header
	class="flex h-14 shrink-0 items-center border-b border-[var(--portal-border-color)] bg-[var(--portal-card-bg)] px-4"
>
	<!-- Lead: hamburger (mobile) + module name -->
	<div class="flex items-center gap-3">
		<button
			type="button"
			class="flex min-h-[48px] min-w-[48px] items-center justify-center rounded-lg transition-colors hover:bg-[var(--portal-hover-bg)] md:hidden"
			onclick={onmenuclick}
			aria-label="Toggle navigation"
		>
			<Menu size={20} />
		</button>

		{#if activeModule}
			<div class="flex items-center gap-2">
				<activeModule.icon size={20} class="text-[var(--color-primary-500)]" />
				<span
					class="text-base font-semibold"
					style:font-family="'Outfit', system-ui, sans-serif"
				>
					{activeModule.name}
				</span>
			</div>
		{/if}
	</div>

	<!-- Trail: theme + user -->
	<div class="ml-auto flex items-center gap-1">
		<ThemePicker />
		<UserMenu {user} compact={true} />
	</div>
</header>
