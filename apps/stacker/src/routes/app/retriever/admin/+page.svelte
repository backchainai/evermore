<script lang="ts">
	import { PUBLIC_RETRIEVER_API_URL } from '$env/static/public';
	import { onMount } from 'svelte';
	import { RetrieverApi } from '$lib/modules/retriever/api/client';
	import type { DocumentResponse } from '$lib/modules/retriever/api/types';
	import DocumentList from '$lib/modules/retriever/components/DocumentList.svelte';
	import DocumentUpload from '$lib/modules/retriever/components/DocumentUpload.svelte';
	import ErrorAlert from '$lib/portal/shared/ErrorAlert.svelte';

	let { data } = $props();

	let documents: DocumentResponse[] = $state([]);
	let isLoading = $state(true);
	let isUploading = $state(false);
	let error: string | null = $state(null);
	let success: string | null = $state(null);

	const api = $derived(
		new RetrieverApi(
			PUBLIC_RETRIEVER_API_URL || 'http://localhost:8001',
			data.session?.access_token ?? ''
		)
	);

	onMount(() => {
		if (data.session) {
			loadDocuments();
		}
	});

	async function loadDocuments() {
		isLoading = true;
		try {
			const result = await api.listDocuments();
			documents = result.documents;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load documents.';
		} finally {
			isLoading = false;
		}
	}

	async function handleUpload(file: File) {
		error = null;
		success = null;
		isUploading = true;

		try {
			const result = await api.uploadDocument(file);
			success = `Uploaded "${result.title}" — ${result.chunks_created} chunks indexed.`;
			await loadDocuments();
		} catch (err) {
			error = err instanceof Error ? `Upload failed: ${err.message}` : 'Upload failed. Please try again.';
		} finally {
			isUploading = false;
		}
	}

	async function handleDelete(id: string) {
		error = null;
		success = null;

		try {
			await api.deleteDocument(id);
			success = 'Document deleted.';
			await loadDocuments();
		} catch (err) {
			error = err instanceof Error ? `Delete failed: ${err.message}` : 'Delete failed. Please try again.';
		}
	}
</script>

<svelte:head>
	<title>Documents – Retriever</title>
</svelte:head>

<div class="mx-auto max-w-4xl p-4">
	<h1 class="mb-6 text-2xl font-bold">Document Management</h1>

	<section class="mb-8">
		<h2 class="mb-3 text-lg font-medium">Upload Document</h2>
		<DocumentUpload onupload={handleUpload} disabled={isUploading} />
		{#if isUploading}
			<p class="mt-2 animate-pulse text-sm text-surface-400">Uploading and indexing...</p>
		{/if}
	</section>

	{#if success}
		<div class="mb-4 rounded-md bg-success-500/20 p-3 text-sm text-success-400">
			{success}
			<button class="ml-2 underline" onclick={() => (success = null)}>Dismiss</button>
		</div>
	{/if}

	{#if error}
		<div class="mb-4">
			<ErrorAlert message={error} ondismiss={() => (error = null)} />
		</div>
	{/if}

	<section>
		<h2 class="mb-3 text-lg font-medium">Documents ({documents.length})</h2>
		{#if isLoading}
			<p class="animate-pulse text-surface-400">Loading documents...</p>
		{:else}
			<DocumentList {documents} ondelete={handleDelete} disabled={isUploading} />
		{/if}
	</section>
</div>
