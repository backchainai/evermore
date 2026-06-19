<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let { data } = $props();

	onMount(() => {
		if (data.session) {
			goto('/app/retriever/chat', { replaceState: true });
		}
	});
</script>

<svelte:head>
	<title>Ask Retriever</title>
</svelte:head>

<div class="mx-auto mt-8 max-w-2xl text-center">
	<h2 class="mb-4 text-3xl font-bold">Ask Retriever</h2>
	<p class="text-surface-600-400">AI-powered Q&A for shelter volunteers</p>
	<div class="mt-8">
		<a href="/login" class="btn preset-filled-primary-500">Sign In to Get Started</a>
	</div>
</div>
