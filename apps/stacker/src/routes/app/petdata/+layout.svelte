<script lang="ts">
	import SubscriptionGate from '$lib/portal/components/SubscriptionGate.svelte';
	import { PETDATA_MODULE } from '$lib/modules/petdata/index';

	let { data, children } = $props();
</script>

{#if data.moduleAccess}
	{@render children()}
{:else}
	<SubscriptionGate module={{ ...PETDATA_MODULE, status: 'locked' }} onclose={() => history.back()} />
{/if}
