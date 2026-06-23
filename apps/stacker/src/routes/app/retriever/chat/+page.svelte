<script lang="ts">
	import { PUBLIC_RETRIEVER_API_URL } from '$env/static/public';
	import { onMount } from 'svelte';
	import { RetrieverApi } from '$lib/modules/retriever/api/client';
	import type { AskResponse } from '$lib/modules/retriever/api/types';
	import ChatMessage from '$lib/modules/retriever/components/ChatMessage.svelte';
	import ChatInput from '$lib/modules/retriever/components/ChatInput.svelte';
	import ConfidenceBadge from '$lib/modules/retriever/components/ConfidenceBadge.svelte';
	import SourceCitation from '$lib/modules/retriever/components/SourceCitation.svelte';
	import ClearHistoryButton from '$lib/modules/retriever/components/ClearHistoryButton.svelte';
	import ErrorAlert from '$lib/portal/shared/ErrorAlert.svelte';

	let { data } = $props();

	interface ChatMsg {
		role: 'user' | 'assistant';
		content: string;
		createdAt?: string;
		liveResponse?: AskResponse;
	}

	let messages: ChatMsg[] = $state([]);
	let isLoading = $state(false);
	let error: string | null = $state(null);
	let messagesEl: HTMLDivElement | undefined = $state();

	const api = $derived(
		new RetrieverApi(
			PUBLIC_RETRIEVER_API_URL || 'http://localhost:8001',
			data.session?.access_token ?? ''
		)
	);

	function scrollToBottom() {
		if (messagesEl) {
			messagesEl.scrollTop = messagesEl.scrollHeight;
		}
	}

	$effect(() => {
		// eslint-disable-next-line @typescript-eslint/no-unused-expressions
		messages.length;
		requestAnimationFrame(scrollToBottom);
	});

	onMount(() => {
		if (data.session) {
			loadHistory();
		}
	});

	async function loadHistory() {
		try {
			const history = await api.getHistory();
			messages = history.messages.map((m) => ({
				role: m.role,
				content: m.content,
				createdAt: m.created_at
			}));
		} catch {
			// Silently fail — user can still chat without history
		}
	}

	async function handleSubmit(question: string) {
		error = null;
		messages = [...messages, { role: 'user', content: question }];
		isLoading = true;

		try {
			const response = await api.ask(question);
			messages = [
				...messages,
				{
					role: 'assistant',
					content: response.answer,
					liveResponse: response
				}
			];
		} catch (err) {
			if (err instanceof Error) {
				error = err.message;
			} else {
				error = 'Network error. Please check your connection and try again.';
			}
		} finally {
			isLoading = false;
		}
	}

	async function handleClear() {
		try {
			await api.clearHistory();
			messages = [];
		} catch {
			error = 'Failed to clear history.';
		}
	}
</script>

<svelte:head>
	<title>Chat – Retriever</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="border-surface-300-700 flex items-center justify-between border-b px-4 py-2">
		<h2 class="font-medium">Chat</h2>
		{#if messages.length > 0}
			<ClearHistoryButton onclear={handleClear} disabled={isLoading} />
		{/if}
	</div>

	<div class="flex-1 overflow-y-auto p-4" bind:this={messagesEl}>
		<div class="mx-auto max-w-3xl space-y-4">
			{#if messages.length === 0 && !isLoading}
				<div class="mt-20 text-center text-surface-500">
					<p class="text-lg font-medium">Ask Retriever a question</p>
					<p class="mt-1 text-sm">Get answers from shelter policies and procedures</p>
				</div>
			{/if}

			{#each messages as msg}
				<div>
					<ChatMessage
						role={msg.role}
						content={msg.content}
						createdAt={msg.createdAt}
					/>
					{#if msg.liveResponse}
						<div class="ml-11 mt-1 space-y-1">
							<ConfidenceBadge
								level={msg.liveResponse.confidence_level}
								score={msg.liveResponse.confidence_score}
							/>
							<SourceCitation chunks={msg.liveResponse.chunks_used} />
						</div>
					{/if}
				</div>
			{/each}

			{#if isLoading}
				<div class="flex gap-3">
					<div
						class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-tertiary-500 text-sm font-bold"
					>
						R
					</div>
					<div class="preset-filled-surface-200-800 rounded-lg p-3">
						<span class="animate-pulse">Thinking...</span>
					</div>
				</div>
			{/if}

			{#if error}
				<ErrorAlert message={error} ondismiss={() => (error = null)} />
			{/if}
		</div>
	</div>

	<ChatInput onsubmit={handleSubmit} disabled={isLoading} />
</div>
