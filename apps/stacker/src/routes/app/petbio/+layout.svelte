<script lang="ts">
	import SubscriptionGate from '$lib/portal/components/SubscriptionGate.svelte';
	import { PETBIO_MODULE } from '$lib/modules/petbio/index';

	let { data, children } = $props();
</script>

{#if data.moduleAccess}
	{@render children()}
{:else}
	<SubscriptionGate module={{ ...PETBIO_MODULE, status: 'locked' }} onclose={() => history.back()} />
{/if}
