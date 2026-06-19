# Stacker

Unified portal frontend for FOHA shelter management tools. Built with SvelteKit, it hosts independent backend service modules (Retriever, PetBio) behind a single authenticated UI, gating access per subscription.

- **Stack:** SvelteKit + Svelte 5 runes + Skeleton UI v4, Tailwind CSS v4
- **Auth:** Supabase Auth (SSR via `@supabase/ssr`)
- **Deploy:** Cloudflare Pages

Stacker is one of the four [Evermore](../platform) repos. See `CLAUDE.md` for architecture and development guidance.

## Development

```bash
npm install      # install dependencies
npm run dev      # development server
npm run check    # type checking (TypeScript + Svelte)
npm run build    # production build
npm run test:e2e # Playwright E2E tests (requires build first)
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0 (Apache-2.0). See [LICENSE](LICENSE) for the full text and [NOTICE](NOTICE) for attribution.

Copyright (C) 2026 Backchain LLC
