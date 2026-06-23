<script lang="ts">
	interface Props {
		onupload: (file: File) => void;
		disabled?: boolean;
	}

	let { onupload, disabled = false }: Props = $props();

	let selectedFile: File | null = $state(null);
	let error: string | null = $state(null);
	let inputEl: HTMLInputElement | undefined = $state();

	const allowedTypes = ['.md', '.txt', '.pdf', '.docx', '.pptx', '.xlsx', '.html', '.htm'];
	const imageTypes = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp'];
	const allTypes = [...allowedTypes, ...imageTypes];
	const maxSizeMbText = 1;
	const maxSizeMbBinary = 20;
	const textTypes = new Set(['.md', '.txt']);

	function openFilePicker() {
		inputEl?.click();
	}

	function handleFileChange(e: Event) {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		error = null;

		if (!file) {
			selectedFile = null;
			return;
		}

		const ext = '.' + file.name.split('.').pop()?.toLowerCase();
		if (!allTypes.includes(ext)) {
			error = `Unsupported format. Accepted: ${allowedTypes.join(', ')}, images`;
			selectedFile = null;
			return;
		}

		const maxSizeMb = textTypes.has(ext) ? maxSizeMbText : maxSizeMbBinary;
		if (file.size > maxSizeMb * 1024 * 1024) {
			error = `File must be under ${maxSizeMb} MB.`;
			selectedFile = null;
			return;
		}

		selectedFile = file;
	}

	function handleUpload() {
		if (!selectedFile) return;
		onupload(selectedFile);
		selectedFile = null;
		if (inputEl) inputEl.value = '';
	}
</script>

<div class="rounded-lg border-2 border-dashed border-surface-500/30 p-6">
	<!-- svelte-ignore a11y_consider_explicit_label -->
	<input
		bind:this={inputEl}
		type="file"
		accept={allTypes.join(',')}
		onchange={handleFileChange}
		style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)"
		tabindex="-1"
		{disabled}
	/>
	<div class="flex flex-col items-center gap-4 sm:flex-row">
		<button
			type="button"
			class="rounded-md bg-surface-200 px-4 py-2 text-sm font-medium text-surface-900 hover:bg-surface-300"
			onclick={openFilePicker}
			{disabled}
		>
			Choose File...
		</button>
		<span class="text-sm text-surface-500">
			{selectedFile
				? selectedFile.name
				: 'PDF, Word, PowerPoint, Excel, Markdown, text, HTML, images (max 20 MB)'}
		</span>
		<button
			type="button"
			class="rounded-md bg-primary-500 px-4 py-2 text-sm font-medium text-white hover:bg-primary-600 disabled:opacity-50"
			onclick={handleUpload}
			disabled={!selectedFile || disabled}
		>
			Upload
		</button>
	</div>
	{#if error}
		<p class="mt-3 text-sm text-error-500">{error}</p>
	{/if}
</div>
