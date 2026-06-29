<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let { data } = $props();

	onMount(() => {
		if (data.session) {
			goto('/app', { replaceState: true });
		}
	});
</script>

<svelte:head>
	<title>Evermore</title>
</svelte:head>

<div class="mx-auto mt-8 max-w-2xl text-center">
	<h2 class="mb-4 text-3xl font-bold">Evermore</h2>
	<p class="text-surface-600-400">AI tools for nonprofit animal shelters</p>
	<div class="mt-8">
		<a href="/login" class="btn preset-filled-primary-500">Sign In to Get Started</a>
	</div>
</div>
