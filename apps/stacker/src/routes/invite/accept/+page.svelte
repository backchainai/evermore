<script lang="ts">
	import { enhance } from '$app/forms';

	let { data, form } = $props();
	let isSubmitting = $state(false);
</script>

<svelte:head>
	<title>Accept Invitation</title>
</svelte:head>

<div class="flex min-h-[80vh] items-center justify-center">
	<div class="w-full max-w-sm space-y-6">
		<div class="text-center">
			<h1 class="text-2xl font-bold">Accept Invitation</h1>
			<p class="text-surface-600-400 mt-2">Set a password to finish creating your account</p>
		</div>

		{#if !data.invited}
			<div class="preset-filled-error-500 rounded-md p-3 text-sm">
				This invitation link is invalid or has expired. Ask your administrator to send a new invite.
			</div>
			<a href="/login" class="btn preset-filled-primary-500 w-full">Back to Sign In</a>
		{:else}
			{#if form?.error}
				<div class="preset-filled-error-500 rounded-md p-3 text-sm">
					{form.error}
				</div>
			{/if}

			{#if data.email}
				<p class="text-surface-600-400 text-center text-sm">
					Creating account for <span class="font-medium">{data.email}</span>
				</p>
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
					<span class="text-sm font-medium">Password</span>
					<input
						type="password"
						name="password"
						required
						minlength="8"
						autocomplete="new-password"
						class="input mt-1 w-full"
						disabled={isSubmitting}
					/>
				</label>

				<label class="block">
					<span class="text-sm font-medium">Confirm password</span>
					<input
						type="password"
						name="confirm"
						required
						minlength="8"
						autocomplete="new-password"
						class="input mt-1 w-full"
						disabled={isSubmitting}
					/>
				</label>

				<button type="submit" class="btn preset-filled-primary-500 w-full" disabled={isSubmitting}>
					{#if isSubmitting}
						Setting password...
					{:else}
						Create account
					{/if}
				</button>
			</form>
		{/if}
	</div>
</div>
