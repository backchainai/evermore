<script lang="ts">
	import { page } from '$app/state';
</script>

<svelte:head>
	<title>Error {page.status}</title>
</svelte:head>

<div class="mx-auto mt-20 max-w-md text-center">
	<h1 class="text-4xl font-bold text-error-500">{page.status}</h1>
	<p class="mt-4 text-lg text-surface-400">{page.error?.message ?? 'Something went wrong'}</p>
	<a href="/" class="btn preset-filled-primary-500 mt-8">Go Home</a>
</div>
