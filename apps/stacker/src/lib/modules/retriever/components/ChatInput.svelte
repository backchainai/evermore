<script lang="ts">
	interface Props {
		onsubmit: (message: string) => void;
		disabled?: boolean;
	}

	let { onsubmit, disabled = false }: Props = $props();

	let message = $state('');
	const maxLength = 2000;
	const charCount = $derived(message.length);
	const canSubmit = $derived(message.trim().length > 0 && !disabled);

	function handleSubmit() {
		if (!canSubmit) return;
		onsubmit(message.trim());
		message = '';
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit();
		}
	}
</script>

<div class="border-surface-300-700 border-t p-4">
	<div class="mx-auto flex max-w-3xl gap-2">
		<div class="flex flex-1 flex-col">
			<textarea
				bind:value={message}
				onkeydown={handleKeydown}
				placeholder="Ask a question..."
				maxlength={maxLength}
				rows={1}
				class="textarea w-full resize-none"
				{disabled}
			></textarea>
			<span class="mt-1 self-end text-xs text-surface-500">
				{charCount}/{maxLength}
			</span>
		</div>
		<button
			onclick={handleSubmit}
			class="btn preset-filled-primary-500 min-h-[48px] min-w-[48px] self-end"
			disabled={!canSubmit}
		>
			{#if disabled}
				<span class="animate-pulse">...</span>
			{:else}
				Send
			{/if}
		</button>
	</div>
</div>
