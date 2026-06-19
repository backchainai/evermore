<script lang="ts">
	interface Props {
		onclear: () => void;
		disabled?: boolean;
	}

	let { onclear, disabled = false }: Props = $props();
	let showConfirm = $state(false);
</script>

{#if showConfirm}
	<div class="flex items-center gap-2">
		<span class="text-sm">Clear all messages?</span>
		<button
			class="btn btn-sm preset-filled-error-500"
			onclick={() => {
				onclear();
				showConfirm = false;
			}}
			{disabled}
		>
			Yes
		</button>
		<button class="btn btn-sm preset-tonal" onclick={() => (showConfirm = false)} {disabled}>
			No
		</button>
	</div>
{:else}
	<button class="btn btn-sm preset-tonal" onclick={() => (showConfirm = true)} {disabled}>
		Clear History
	</button>
{/if}
