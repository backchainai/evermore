<script lang="ts">
	import type { DocumentResponse } from '$lib/api/types';

	interface Props {
		documents: DocumentResponse[];
		ondelete: (id: string) => void;
		disabled?: boolean;
	}

	let { documents, ondelete, disabled = false }: Props = $props();
	let confirmId: string | null = $state(null);

	function formatBytes(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString();
	}

	const mimeLabels: Record<string, string> = {
		'text/markdown': 'Markdown',
		'text/plain': 'Text',
		'application/pdf': 'PDF',
		'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word',
		'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PowerPoint',
		'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Excel',
		'text/html': 'HTML',
		'image/png': 'PNG',
		'image/jpeg': 'JPEG',
		'image/tiff': 'TIFF',
		'image/bmp': 'BMP'
	};

	function formatType(mime: string): string {
		return mimeLabels[mime] ?? mime;
	}
</script>

{#if documents.length === 0}
	<p class="py-8 text-center text-surface-500">No documents uploaded yet.</p>
{:else}
	<!-- Desktop table -->
	<div class="hidden md:block">
		<table class="w-full text-left text-sm">
			<thead>
				<tr class="border-b border-surface-500/20">
					<th class="p-2 font-medium">Title</th>
					<th class="p-2 font-medium">Filename</th>
					<th class="p-2 font-medium">Type</th>
					<th class="p-2 font-medium">Size</th>
					<th class="p-2 font-medium">Indexed</th>
					<th class="p-2 font-medium">Date</th>
					<th class="p-2 font-medium"></th>
				</tr>
			</thead>
			<tbody>
				{#each documents as doc}
					<tr class="border-b border-surface-500/10">
						<td class="p-2">{doc.title}</td>
						<td class="p-2 text-surface-400">{doc.filename}</td>
						<td class="p-2">{formatType(doc.file_type)}</td>
						<td class="p-2">{formatBytes(doc.file_size_bytes)}</td>
						<td class="p-2">
							{#if doc.is_indexed}
								<span class="text-success-500">Yes</span>
							{:else}
								<span class="text-warning-500">No</span>
							{/if}
						</td>
						<td class="p-2">{formatDate(doc.created_at)}</td>
						<td class="p-2">
							{#if confirmId === doc.id}
								<div class="flex gap-1">
									<button
										class="btn btn-sm preset-filled-error-500"
										onclick={() => {
											ondelete(doc.id);
											confirmId = null;
										}}
										{disabled}
									>
										Confirm
									</button>
									<button
										class="btn btn-sm preset-tonal"
										onclick={() => (confirmId = null)}
									>
										Cancel
									</button>
								</div>
							{:else}
								<button
									class="btn btn-sm preset-tonal-error"
									onclick={() => (confirmId = doc.id)}
									{disabled}
								>
									Delete
								</button>
							{/if}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>

	<!-- Mobile cards -->
	<div class="space-y-3 md:hidden">
		{#each documents as doc}
			<div class="rounded-lg border border-surface-500/20 p-3">
				<div class="flex items-start justify-between">
					<div>
						<p class="font-medium">{doc.title}</p>
						<p class="text-sm text-surface-400">{doc.filename}</p>
					</div>
					{#if doc.is_indexed}
						<span class="text-xs text-success-500">Indexed</span>
					{:else}
						<span class="text-xs text-warning-500">Pending</span>
					{/if}
				</div>
				<div class="mt-2 flex items-center justify-between text-sm text-surface-500">
					<span>{formatType(doc.file_type)} &middot; {formatBytes(doc.file_size_bytes)}</span>
					<span>{formatDate(doc.created_at)}</span>
				</div>
				<div class="mt-2">
					{#if confirmId === doc.id}
						<div class="flex gap-2">
							<button
								class="btn btn-sm preset-filled-error-500"
								onclick={() => {
									ondelete(doc.id);
									confirmId = null;
								}}
								{disabled}
							>
								Confirm Delete
							</button>
							<button class="btn btn-sm preset-tonal" onclick={() => (confirmId = null)}>
								Cancel
							</button>
						</div>
					{:else}
						<button
							class="btn btn-sm preset-tonal-error"
							onclick={() => (confirmId = doc.id)}
							{disabled}
						>
							Delete
						</button>
					{/if}
				</div>
			</div>
		{/each}
	</div>
{/if}
