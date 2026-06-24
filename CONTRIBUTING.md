# Contributing to Evermore

Thanks for your interest in Evermore, an AI platform for nonprofit animal shelters.

## How to contribute

> This repository is private during pre-release development and goes public once the v1 wedge is demoable. Until then, the issue tracker and project board linked below require repository access.

- Browse [open issues](https://github.com/backchainai/evermore/issues) and the project board to find work.
- Open an issue to propose a change or report a bug before starting substantial work.
- Fork the repository, create a branch, and open a pull request against `main`.
- Keep pull requests focused, and describe what changed and why.

## Development

Start with [`docs/local-development.md`](docs/local-development.md): it brings up the portal (stacker) with the Retriever module on your machine and covers prerequisites, the service topology, and troubleshooting. Run the full setup in the order given there; `make env` then `make dev` alone is not sufficient (an LLM gateway token and the Supabase anon key are required in between).

Per-module build and test commands:

- **Python services** (`services/retriever`, `services/petdata`): from the service directory, `uv sync --dev` to install, `uv run pytest` to run tests, `uv run ruff check src/ tests/` and `uv run python -m mypy src/` to lint and type-check.
- **Stacker portal** (`apps/stacker`): from the app directory, `npm install`, then `npm run dev`, `npm run check`, and `npm run build`.

The platform tech-stack standard governs all modules. See [`docs/evermore-vision-and-architecture.md`](docs/evermore-vision-and-architecture.md) for product and architecture, and [`docs/plans/repo-restructure-and-rename.md`](docs/plans/repo-restructure-and-rename.md) for current state and sequencing.

## License of Contributions

This project is licensed under Apache License 2.0. By submitting a contribution, you agree that your contribution is licensed under the same terms.
