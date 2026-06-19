<script lang="ts">
	import { enhance } from '$app/forms';

	let { form } = $props();
	let isSubmitting = $state(false);
</script>

<svelte:head>
	<title>Sign In</title>
</svelte:head>

<div class="flex min-h-[80vh] items-center justify-center">
	<div class="w-full max-w-sm space-y-6">
		<div class="text-center">
			<h1 class="text-2xl font-bold">Sign In</h1>
			<p class="text-surface-600-400 mt-2">Shelter volunteer portal</p>
		</div>

		{#if form?.error}
			<div class="preset-filled-error-500 rounded-md p-3 text-sm">
				{form.error}
			</div>
		{/if}

		<form
			method="POST"
			use:enhance={() => {
				isSubmitting = true;
				return async ({ update }) => {
					isSubmitting = false;
					await update();
				};
			}}
			class="space-y-4"
		>
			<label class="block">
				<span class="text-sm font-medium">Email</span>
				<input
					type="email"
					name="email"
					value={form?.email ?? ''}
					required
					autocomplete="email"
					class="input mt-1 w-full"
					disabled={isSubmitting}
				/>
			</label>

			<label class="block">
				<span class="text-sm font-medium">Password</span>
				<input
					type="password"
					name="password"
					required
					autocomplete="current-password"
					class="input mt-1 w-full"
					disabled={isSubmitting}
				/>
			</label>

			<button type="submit" class="btn preset-filled-primary-500 w-full" disabled={isSubmitting}>
				{#if isSubmitting}
					Signing in...
				{:else}
					Sign In
				{/if}
			</button>
		</form>
	</div>
</div>
