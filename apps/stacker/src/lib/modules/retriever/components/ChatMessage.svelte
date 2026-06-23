<script lang="ts">
	import { marked } from 'marked';

	interface Props {
		role: 'user' | 'assistant';
		content: string;
		createdAt?: string;
	}

	let { role, content, createdAt }: Props = $props();

	const initials = $derived(role === 'user' ? 'U' : 'R');
	const alignment = $derived(role === 'user' ? 'justify-end' : 'justify-start');
	const bubbleBg = $derived(
		role === 'user' ? 'preset-filled-primary-500' : 'preset-filled-surface-200-800'
	);
	const timeStr = $derived(createdAt ? new Date(createdAt).toLocaleTimeString() : '');
	const renderedContent = $derived(
		role === 'assistant' ? marked.parse(content, { async: false }) as string : ''
	);
</script>

<div class="flex gap-3 {alignment}">
	{#if role === 'assistant'}
		<div
			class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-tertiary-500 text-sm font-bold"
		>
			{initials}
		</div>
	{/if}

	<div class="max-w-[75%] space-y-1">
		<div class="rounded-lg p-3 {bubbleBg}">
			{#if role === 'assistant'}
				<div class="chat-prose">{@html renderedContent}</div>
			{:else}
				<p class="whitespace-pre-wrap">{content}</p>
			{/if}
		</div>
		{#if timeStr}
			<p class="text-xs text-surface-500">{timeStr}</p>
		{/if}
	</div>

	{#if role === 'user'}
		<div
			class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-500 text-sm font-bold"
		>
			{initials}
		</div>
	{/if}
</div>

<style>
	.chat-prose :global(p) {
		margin: 0.5em 0;
	}
	.chat-prose :global(p:first-child) {
		margin-top: 0;
	}
	.chat-prose :global(p:last-child) {
		margin-bottom: 0;
	}
	.chat-prose :global(ul),
	.chat-prose :global(ol) {
		margin: 0.5em 0;
		padding-left: 1.5em;
	}
	.chat-prose :global(ul) {
		list-style-type: disc;
	}
	.chat-prose :global(ol) {
		list-style-type: decimal;
	}
	.chat-prose :global(li) {
		margin: 0.25em 0;
	}
	.chat-prose :global(code) {
		font-family: var(--font-mono, monospace);
		font-size: 0.875em;
		padding: 0.15em 0.35em;
		border-radius: 4px;
		background: rgba(0, 0, 0, 0.08);
	}
	.chat-prose :global(pre) {
		margin: 0.75em 0;
		padding: 0.75em;
		border-radius: 6px;
		background: rgba(0, 0, 0, 0.08);
		overflow-x: auto;
	}
	.chat-prose :global(pre code) {
		padding: 0;
		background: none;
	}
	.chat-prose :global(strong) {
		font-weight: 600;
	}
	.chat-prose :global(h1),
	.chat-prose :global(h2),
	.chat-prose :global(h3) {
		font-weight: 600;
		margin: 0.75em 0 0.25em;
	}
	.chat-prose :global(blockquote) {
		border-left: 3px solid currentColor;
		opacity: 0.8;
		padding-left: 0.75em;
		margin: 0.5em 0;
	}
	.chat-prose :global(a) {
		text-decoration: underline;
		text-underline-offset: 2px;
	}
</style>
