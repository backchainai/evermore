export interface AskRequest {
	question: string;
}

export interface ChunkWithScore {
	content: string;
	source: string;
	section: string;
	score: number;
	title: string;
}

export type ConfidenceLevel = 'high' | 'medium' | 'low';
export type MessageRole = 'user' | 'assistant';

export interface AskResponse {
	answer: string;
	chunks_used: ChunkWithScore[];
	confidence_level: ConfidenceLevel;
	confidence_score: number;
	blocked: boolean;
	blocked_reason: string | null;
}

export interface MessageResponse {
	id: string;
	role: MessageRole;
	content: string;
	created_at: string;
}

export interface MessageHistoryResponse {
	messages: MessageResponse[];
	count: number;
}

export interface ClearHistoryResponse {
	deleted_count: number;
	message: string;
}

export interface DocumentResponse {
	id: string;
	filename: string;
	title: string;
	file_type: string;
	file_size_bytes: number;
	is_indexed: boolean;
	created_at: string;
	description: string | null;
}

export interface DocumentListResponse {
	documents: DocumentResponse[];
	count: number;
}

export interface DocumentUploadResponse {
	id: string;
	filename: string;
	title: string;
	chunks_created: number;
	message: string;
}

export interface DocumentDeleteResponse {
	message: string;
}
