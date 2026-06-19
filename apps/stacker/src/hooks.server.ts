import { type Handle, redirect } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';
import { createSupabaseServerClient } from '$lib/server/supabase';

const supabaseHandle: Handle = async ({ event, resolve }) => {
	event.locals.supabase = createSupabaseServerClient(event.cookies);

	event.locals.safeGetSession = async () => {
		const {
			data: { session }
		} = await event.locals.supabase.auth.getSession();
		if (!session) {
			return { session: null, user: null };
		}
		const {
			data: { user },
			error
		} = await event.locals.supabase.auth.getUser();
		if (error) {
			return { session: null, user: null };
		}
		return { session, user };
	};

	return resolve(event, {
		filterSerializedResponseHeaders(name) {
			return name === 'content-range' || name === 'x-supabase-api-version';
		}
	});
};

const protectedPaths = ['/app'];

const authGuard: Handle = async ({ event, resolve }) => {
	const { session, user } = await event.locals.safeGetSession();
	event.locals.session = session;
	event.locals.user = user;

	const isProtected = protectedPaths.some((p) => event.url.pathname.startsWith(p));

	if (!session && isProtected) {
		redirect(303, '/login');
	}

	if (session && event.url.pathname === '/login') {
		redirect(303, '/app/retriever/chat');
	}

	return resolve(event);
};

export const handle: Handle = sequence(supabaseHandle, authGuard);
