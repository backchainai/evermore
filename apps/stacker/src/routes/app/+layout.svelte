<script lang="ts">
	import PortalShell from '$lib/portal/components/PortalShell.svelte';
	import { getModulesWithStatus, getActiveModule } from '$lib/portal/config';
	import { page } from '$app/stores';

	let { data, children } = $props();

	const subscriptions = $derived(new Set(data.subscriptions || []));
	const modules = $derived(getModulesWithStatus(subscriptions));
	const activeModule = $derived(getActiveModule($page.url.pathname));
</script>

<PortalShell
	{modules}
	activeModuleId={activeModule?.id ?? null}
	user={data.user ? { email: data.user.email ?? '', role: data.user.role } : null}
>
	{@render children()}
</PortalShell>
