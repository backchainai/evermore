<script lang="ts">
	import { getModulesWithStatus } from '$lib/portal/config';
	import ModuleIcon from '$lib/portal/components/ModuleIcon.svelte';
	import { firstNameFromEmail } from '$lib/portal/user-display';
	import { AlertTriangle, Inbox, PencilLine, AlertOctagon } from '@lucide/svelte';
	import type { Component } from 'svelte';

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

	type NotificationStatus = 'warn' | 'info' | 'new' | 'crit';

	interface NotificationItem {
		label: string;
		status: NotificationStatus;
		icon: Component;
		href: string;
	}

	// Status colors map to design-system tokens (no --color-info token exists; info uses primary).
	const STATUS_TOKEN: Record<NotificationStatus, string> = {
		warn: 'var(--color-warning-500)',
		info: 'var(--color-primary-500)',
		new: 'var(--color-success-500)',
		crit: 'var(--color-error-500)'
	};

	const notifications: NotificationItem[] = [
		{
			label: 'Stale pet data',
			status: 'warn',
			icon: AlertTriangle,
			href: '/app/petdata/animals'
		},
		{
			label: 'New animals to review',
			status: 'info',
			icon: Inbox,
			href: '/app/petdata/animals'
		},
		{
			label: 'New in BioWriter',
			status: 'new',
			icon: PencilLine,
			// TODO: deep-link to BioWriter when its route exists
			href: '/app'
		},
		{
			label: 'Scheduled maintenance',
			status: 'crit',
			icon: AlertOctagon,
			href: '/app'
		}
	];
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
				<ModuleIcon icon={mod.icon} size={46} svgSize={24} />
				<h2 class="card-title">{mod.name}</h2>
				<p class="card-desc">{mod.description}</p>
				<span class="card-open">Open →</span>
			</a>
		{/each}
	</div>

	<section class="notifications-card">
		<h2 class="panel-title">Notifications</h2>
		<ul class="notifications-list">
			{#each notifications as item (item.label)}
				<li>
					<a href={item.href} class="notification-row">
						<span
							class="chip"
							style:color={STATUS_TOKEN[item.status]}
							style:background-color="color-mix(in srgb, {STATUS_TOKEN[
								item.status
							]} 14%, transparent)"
							aria-hidden="true"
						>
							<item.icon size={16} />
						</span>
						<span class="notification-label">{item.label}</span>
						<span class="notification-open" aria-hidden="true">→</span>
					</a>
				</li>
			{/each}
		</ul>
	</section>
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

	.notifications-card {
		margin-top: 2rem;
		padding: 22px;
		border: 1px solid var(--portal-border-color);
		border-radius: 8px;
		background-color: var(--portal-card-bg);
	}

	.panel-title {
		font-family: 'Outfit', system-ui, sans-serif;
		font-size: 16px;
		font-weight: 600;
		margin-bottom: 0.75rem;
	}

	.notifications-list {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.notification-row {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 10px 8px;
		border-radius: 8px;
		text-decoration: none;
		color: inherit;
		transition: background-color 0.15s ease;
	}

	.notification-row:hover {
		background-color: var(--portal-hover-bg);
		text-decoration: none;
	}

	.chip {
		display: inline-flex;
		height: 28px;
		width: 28px;
		flex-shrink: 0;
		align-items: center;
		justify-content: center;
		border-radius: 8px;
	}

	.notification-label {
		flex: 1;
		min-width: 0;
		font-size: 13.5px;
		font-weight: 500;
	}

	.notification-open {
		font-size: 13px;
		font-weight: 600;
		color: var(--color-primary-500);
		opacity: 0;
		transition: opacity 0.15s ease;
	}

	.notification-row:hover .notification-open {
		opacity: 1;
	}
</style>
