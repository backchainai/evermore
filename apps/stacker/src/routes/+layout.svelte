<script lang="ts">
	import '../app.css';
	import { invalidate } from '$app/navigation';
	import { onMount } from 'svelte';
	import { initTheme } from '$lib/portal/theme/theme-store.svelte';

	let { data, children } = $props();

	onMount(() => {
		initTheme();

		const {
			data: { subscription }
		} = data.supabase.auth.onAuthStateChange((event: string) => {
			if (event === 'SIGNED_OUT') {
				invalidate('supabase:auth');
			}
		});

		return () => subscription.unsubscribe();
	});
</script>

{@render children()}
