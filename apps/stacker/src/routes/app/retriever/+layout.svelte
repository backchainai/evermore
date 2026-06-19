<script lang="ts">
	import SubscriptionGate from '$lib/portal/components/SubscriptionGate.svelte';
	import { RETRIEVER_MODULE } from '$lib/modules/retriever/index';

	let { data, children } = $props();
</script>

{#if data.moduleAccess}
	{@render children()}
{:else}
	<SubscriptionGate module={{ ...RETRIEVER_MODULE, status: 'locked' }} onclose={() => history.back()} />
{/if}
