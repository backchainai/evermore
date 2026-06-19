import { BaseApiClient } from '$lib/api/base-client';
import type {
	AskRequest,
	AskResponse,
	MessageHistoryResponse,
	ClearHistoryResponse,
	DocumentListResponse,
	DocumentUploadResponse,
	DocumentDeleteResponse
} from './types';

export class RetrieverApi extends BaseApiClient {
	constructor(baseUrl: string, token: string) {
		super(baseUrl, token);
	}

	async ask(question: string): Promise<AskResponse> {
		const body: AskRequest = { question };
		return this.request<AskResponse>('/api/v1/ask', {
			method: 'POST',
			body: JSON.stringify(body)
		});
	}

	async getHistory(): Promise<MessageHistoryResponse> {
		return this.request<MessageHistoryResponse>('/api/v1/history');
	}

	async clearHistory(): Promise<ClearHistoryResponse> {
		return this.request<ClearHistoryResponse>('/api/v1/history', { method: 'DELETE' });
	}

	async listDocuments(): Promise<DocumentListResponse> {
		return this.request<DocumentListResponse>('/api/v1/documents');
	}

	async uploadDocument(file: File): Promise<DocumentUploadResponse> {
		const formData = new FormData();
		formData.append('file', file);
		return this.request<DocumentUploadResponse>('/api/v1/documents/upload', {
			method: 'POST',
			body: formData
		}, 120_000);
	}

	async deleteDocument(id: string): Promise<DocumentDeleteResponse> {
		return this.request<DocumentDeleteResponse>(`/api/v1/documents/${id}`, { method: 'DELETE' });
	}
}
