export class ApiError extends Error {
	constructor(
		public status: number,
		message: string
	) {
		super(message);
		this.name = 'ApiError';
	}
}

export abstract class BaseApiClient {
	protected baseUrl: string;
	protected token: string;
	protected timeoutMs: number;

	constructor(baseUrl: string, token: string, timeoutMs: number = 30_000) {
		this.baseUrl = baseUrl.replace(/\/$/, '');
		this.token = token;
		this.timeoutMs = timeoutMs;
	}

	protected async request<T>(path: string, options: RequestInit = {}, timeoutMs?: number): Promise<T> {
		const url = `${this.baseUrl}${path}`;
		const headers: Record<string, string> = {
			Authorization: `Bearer ${this.token}`,
			...((options.headers as Record<string, string>) ?? {})
		};

		if (!(options.body instanceof FormData)) {
			headers['Content-Type'] = 'application/json';
		}

		const controller = new AbortController();
		const timeout = setTimeout(() => controller.abort(), timeoutMs ?? this.timeoutMs);

		try {
			const response = await fetch(url, {
				...options,
				headers,
				signal: controller.signal
			});

			if (!response.ok) {
				const body = await response.text();
				throw new ApiError(response.status, body || response.statusText);
			}

			return (await response.json()) as T;
		} finally {
			clearTimeout(timeout);
		}
	}
}
