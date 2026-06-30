<script lang="ts">
	/**
	 * Sidebar footer account control. The account button opens a dropdown with
	 * account detail; a separate logout icon button is the primary sign-out
	 * affordance and posts the existing `POST /logout` form.
	 */
	import { LogOut, ChevronDown } from '@lucide/svelte';
	import { initialsFromEmail, displayNameFromEmail } from '$lib/portal/user-display';

	interface Props {
		user: { email: string; role?: string } | null;
	}

	let { user }: Props = $props();

	let open = $state(false);

	let initials = $derived(initialsFromEmail(user?.email));
	let displayName = $derived(displayNameFromEmail(user?.email));

	// TODO(#154): derive org name from org context
	const orgName = 'Your Organization';

	function handleClickOutside(event: MouseEvent): void {
		const target = event.target as HTMLElement;
		if (!target.closest('.user-menu')) {
			open = false;
		}
	}

	function handleKeydown(event: KeyboardEvent): void {
		if (event.key === 'Escape') {
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

<div class="user-menu relative">
	<div class="flex items-center gap-1.5">
		<button
			type="button"
			class="footer-btn flex min-w-0 flex-1 items-center gap-2.5 rounded-lg px-2 py-2 text-left transition-colors"
			onclick={() => (open = !open)}
			aria-expanded={open}
			aria-haspopup="menu"
			aria-label="Account menu"
		>
			<span class="avatar" aria-hidden="true">{initials}</span>
			<span class="flex min-w-0 flex-1 flex-col leading-tight">
				<span class="name truncate">{displayName}</span>
				<span class="org truncate">{orgName}</span>
			</span>
			<ChevronDown size={14} class="shrink-0 opacity-50" />
		</button>

		<form method="POST" action="/logout">
			<button
				type="submit"
				class="logout-btn flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors"
				aria-label="Sign out"
			>
				<LogOut size={16} />
			</button>
		</form>
	</div>

	{#if open}
		<div
			class="absolute bottom-full left-0 right-0 z-50 mb-2 overflow-hidden rounded-xl border border-[var(--portal-border-color)] bg-[var(--portal-card-bg)] shadow-lg"
			role="menu"
		>
			{#if user}
				<div class="border-b border-[var(--portal-border-color)] px-4 py-3">
					<p class="truncate text-sm font-medium">{displayName}</p>
					<p class="truncate text-xs opacity-55">{user.email}</p>
				</div>
			{/if}
			<form method="POST" action="/logout">
				<button
					type="submit"
					class="flex min-h-[44px] w-full items-center gap-3 px-4 py-2 text-sm transition-colors hover:bg-[var(--portal-hover-bg)]"
					role="menuitem"
				>
					<LogOut size={16} class="opacity-60" />
					Sign out
				</button>
			</form>
		</div>
	{/if}
</div>

<style>
	.footer-btn {
		color: var(--portal-sidebar-text);
	}

	.footer-btn:hover {
		background-color: color-mix(in srgb, var(--portal-sidebar-text) 8%, transparent);
	}

	.footer-btn:focus-visible {
		outline: 2px solid var(--color-primary-500);
		outline-offset: 2px;
	}

	.logout-btn {
		color: color-mix(in srgb, var(--portal-sidebar-text) 72%, transparent);
	}

	.logout-btn:hover {
		background-color: color-mix(in srgb, var(--portal-sidebar-text) 8%, transparent);
		color: var(--portal-sidebar-text);
	}

	.logout-btn:focus-visible {
		outline: 2px solid var(--color-primary-500);
		outline-offset: 2px;
	}

	.avatar {
		display: inline-flex;
		height: 32px;
		width: 32px;
		flex-shrink: 0;
		align-items: center;
		justify-content: center;
		border-radius: 9999px;
		background-color: var(--color-primary-500);
		color: #fff;
		font-size: 12px;
		font-weight: 600;
	}

	.name {
		font-size: 13px;
		font-weight: 600;
	}

	.org {
		font-size: 11px;
		color: color-mix(in srgb, var(--portal-sidebar-text) 55%, transparent);
	}
</style>
