# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability in Evermore, please report it privately.
Do not open a public issue for security problems.

Email **security@backchain.ai** with:

- a description of the vulnerability and its impact,
- steps to reproduce (a proof of concept if you have one),
- the affected module (`apps/stacker`, `services/petdata`, `services/retriever`, or `services/biowriter`) and version or commit.

We will acknowledge your report within five business days and keep you updated as we
investigate. Once a fix is available we will coordinate a disclosure timeline with you.

## Supported versions

Evermore is pre-1.0 and under active development. Security fixes are applied to the
`main` branch. There are no separately maintained release branches yet.

## Scope

In scope: the code in this repository. Out of scope: third-party services Evermore
integrates with (Supabase, Cloudflare, LLM providers), which have their own disclosure
programs.
