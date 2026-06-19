<script lang="ts">
	interface Props {
		message: string;
		onretry?: () => void;
		ondismiss?: () => void;
	}

	let { message, onretry, ondismiss }: Props = $props();
</script>

<div class="rounded-lg border border-error-500/30 bg-error-500/10 p-4">
	<p class="text-sm text-error-400">{message}</p>
	<div class="mt-2 flex gap-2">
		{#if onretry}
			<button class="btn btn-sm preset-tonal-error" onclick={onretry}>Try Again</button>
		{/if}
		{#if ondismiss}
			<button class="text-sm text-error-400 underline" onclick={ondismiss}>Dismiss</button>
		{/if}
	</div>
</div>
