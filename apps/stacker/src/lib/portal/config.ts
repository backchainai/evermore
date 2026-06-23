import type { ModuleDefinition, ModuleStatus } from './types';
import { RETRIEVER_MODULE } from '$lib/modules/retriever/index';
import { PETDATA_MODULE } from '$lib/modules/petdata/index';
import { env } from '$env/dynamic/public';

export const MODULE_REGISTRY: ModuleDefinition[] = [
	RETRIEVER_MODULE,
	PETDATA_MODULE
];

// When false, disabled (not-enabled) modules render greyed as "In development".
// Flip to true to drop them from the portal entirely.
const HIDE_DISABLED_MODULES = false;

// PUBLIC_ENABLED_MODULES is a comma-separated allow-list of module ids.
// Unset or empty means every registered module is enabled (preserves prior behavior).
// Read via $env/dynamic/public so an absent var is undefined rather than a build error.
function parseEnabledModules(): Set<string> | null {
	const raw = env.PUBLIC_ENABLED_MODULES?.trim();
	if (!raw) return null; // null = no restriction
	return new Set(
		raw
			.split(',')
			.map((id) => id.trim())
			.filter(Boolean)
	);
}

const ENABLED_MODULES = parseEnabledModules();

export function isModuleEnabled(moduleId: string): boolean {
	return ENABLED_MODULES === null || ENABLED_MODULES.has(moduleId);
}

export function getActiveModule(pathname: string): ModuleDefinition | undefined {
	return MODULE_REGISTRY.find((m) => pathname.startsWith(m.basePath));
}

export function resolveModuleStatus(moduleId: string, subscriptions: Set<string>): ModuleStatus {
	if (!isModuleEnabled(moduleId)) return 'disabled';
	return subscriptions.has(moduleId) ? 'active' : 'locked';
}

export function getModulesWithStatus(subscriptions: Set<string>): ModuleDefinition[] {
	return MODULE_REGISTRY.map((m) => ({
		...m,
		status: resolveModuleStatus(m.id, subscriptions)
	})).filter((m) => !HIDE_DISABLED_MODULES || m.status !== 'disabled');
}
