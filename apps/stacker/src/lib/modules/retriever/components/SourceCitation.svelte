<script lang="ts">
	import type { ChunkWithScore } from '$lib/api/types';

	interface Props {
		chunks: ChunkWithScore[];
	}

	let { chunks }: Props = $props();
	let isOpen = $state(false);
</script>

{#if chunks.length > 0}
	<div class="mt-2">
		<button
			onclick={() => (isOpen = !isOpen)}
			class="text-xs text-primary-400 hover:text-primary-300"
		>
			{isOpen ? 'Hide' : 'Show'} sources ({chunks.length})
		</button>

		{#if isOpen}
			<div class="mt-2 space-y-2">
				{#each chunks as chunk}
					<div class="rounded border border-surface-500/20 p-2 text-xs">
						<div class="mb-1 flex items-center justify-between">
							<span class="font-medium">{chunk.title || chunk.source}</span>
							<span class="text-surface-500">{Math.round(chunk.score * 100)}%</span>
						</div>
						<p class="text-surface-400 line-clamp-3">{chunk.content}</p>
					</div>
				{/each}
			</div>
		{/if}
	</div>
{/if}
