import { BaseApiClient } from '$lib/api/base-client';
import type { AnimalListResponse, AnimalDetailResponse } from './types';

export class PetDataApi extends BaseApiClient {
	constructor(baseUrl: string, token: string) {
		super(baseUrl, token);
	}

	async listAnimals(): Promise<AnimalListResponse> {
		return this.request<AnimalListResponse>('/api/v1/animals');
	}

	async getAnimal(id: string): Promise<AnimalDetailResponse> {
		return this.request<AnimalDetailResponse>(`/api/v1/animals/${encodeURIComponent(id)}`);
	}
}
