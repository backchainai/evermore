<script lang="ts">
	import type { ModuleDefinition } from '$lib/portal/types';
	import { X, Check } from '@lucide/svelte';

	interface Props {
		module: ModuleDefinition;
		onclose: () => void;
	}

	let { module, onclose }: Props = $props();

	let dialogEl: HTMLDivElement | undefined = $state();

	const features = [
		'AI-powered document analysis and search',
		'Real-time collaboration and sharing',
		'Automated workflow processing',
		'Priority support and onboarding'
	];

	function handleKeydown(event: KeyboardEvent): void {
		if (event.key === 'Escape') {
			onclose();
			return;
		}
		// Focus trap
		if (event.key === 'Tab' && dialogEl) {
			const focusable = dialogEl.querySelectorAll<HTMLElement>(
				'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
			);
			if (focusable.length === 0) return;
			const first = focusable[0];
			const last = focusable[focusable.length - 1];
			if (event.shiftKey && document.activeElement === first) {
				event.preventDefault();
				last.focus();
			} else if (!event.shiftKey && document.activeElement === last) {
				event.preventDefault();
				first.focus();
			}
		}
	}

	function handleBackdropClick(event: MouseEvent): void {
		if (event.target === event.currentTarget) {
			onclose();
		}
	}

	$effect(() => {
		// Focus the close button on mount
		if (dialogEl) {
			const closeBtn = dialogEl.querySelector<HTMLElement>('[data-close]');
			closeBtn?.focus();
		}
	});
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
	class="fixed inset-0 z-50 flex items-center justify-center p-4"
	onclick={handleBackdropClick}
>
	<div class="absolute inset-0 bg-black/50 backdrop-blur-sm" aria-hidden="true"></div>

	<div
		bind:this={dialogEl}
		class="relative z-10 w-full max-w-[440px] rounded-xl border border-[var(--portal-border-color)] bg-[var(--portal-card-bg)] shadow-2xl"
		role="dialog"
		aria-modal="true"
		aria-labelledby="gate-title"
	>
		<!-- Close button -->
		<button
			type="button"
			data-close
			class="absolute right-2 top-2 flex min-h-[48px] min-w-[48px] items-center justify-center rounded-lg transition-colors hover:bg-[var(--portal-hover-bg)]"
			onclick={onclose}
			aria-label="Close"
		>
			<X size={20} class="opacity-60" />
		</button>

		<div class="px-6 pb-6 pt-8 text-center">
			<!-- Module icon -->
			<span
				class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--color-primary-500)]/10"
			>
				<module.icon size={28} class="text-[var(--color-primary-500)]" />
			</span>

			<h2
				id="gate-title"
				class="text-lg font-semibold"
				style:font-family="'Outfit', system-ui, sans-serif"
			>
				{module.name}
			</h2>
			<p class="mt-1 text-sm opacity-60">Upgrade to access</p>

			<!-- Feature list -->
			<ul class="mt-6 space-y-3 text-left">
				{#each features as feature}
					<li class="flex items-start gap-2.5 text-sm">
						<Check size={16} class="mt-0.5 shrink-0 text-[var(--color-success-500)]" />
						<span>{feature}</span>
					</li>
				{/each}
			</ul>

			<!-- CTA -->
			<button
				type="button"
				class="mt-6 min-h-[48px] w-full rounded-lg bg-[var(--portal-cta-bg,var(--color-primary-500))] px-4 font-medium text-white transition-colors hover:brightness-90"
			>
				Upgrade to Access {module.name}
			</button>

			<!-- Ghost dismiss -->
			<button
				type="button"
				class="mt-2 min-h-[48px] w-full rounded-lg px-4 text-sm opacity-60 transition-colors hover:bg-[var(--portal-hover-bg)] hover:opacity-100"
				onclick={onclose}
			>
				Maybe later
			</button>
		</div>
	</div>
</div>
