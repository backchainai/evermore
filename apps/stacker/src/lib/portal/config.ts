import type { ModuleDefinition, ModuleStatus } from './types';
import { RETRIEVER_MODULE } from '$lib/modules/retriever/index';
import { PETDATA_MODULE } from '$lib/modules/petdata/index';

export const MODULE_REGISTRY: ModuleDefinition[] = [
	RETRIEVER_MODULE,
	PETDATA_MODULE
];

export function getActiveModule(pathname: string): ModuleDefinition | undefined {
	return MODULE_REGISTRY.find((m) => pathname.startsWith(m.basePath));
}

export function resolveModuleStatus(moduleId: string, subscriptions: Set<string>): ModuleStatus {
	return subscriptions.has(moduleId) ? 'active' : 'locked';
}

export function getModulesWithStatus(subscriptions: Set<string>): ModuleDefinition[] {
	return MODULE_REGISTRY.map((m) => ({
		...m,
		status: resolveModuleStatus(m.id, subscriptions)
	}));
}
