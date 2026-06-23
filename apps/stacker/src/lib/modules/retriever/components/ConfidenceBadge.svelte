<script lang="ts">
	import type { ConfidenceLevel } from '$lib/api/types';

	interface Props {
		level: ConfidenceLevel;
		score?: number;
	}

	let { level, score }: Props = $props();

	const colorClass = $derived(
		level === 'high'
			? 'bg-success-500'
			: level === 'medium'
				? 'bg-warning-500'
				: 'bg-error-500'
	);

	const label = $derived(
		score !== undefined ? `${level} (${Math.round(score * 100)}%)` : level
	);
</script>

<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium {colorClass}">
	{label}
</span>
