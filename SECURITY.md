# Security Policy

## Supported versions

Only the latest commit on the `main` branch receives security fixes. The v1 Streamlit app and the v2 Next.js + FastAPI app are both covered while they live in this repository.

## Reporting a vulnerability

Please do not open a public issue for security problems.

Report it privately by either:

- using **Report a vulnerability** under this repository's **Security** tab, or
- emailing **vsuryansh080405@gmail.com** with the subject `[IMAZINTHECOMICS] Security report`.

Include:

- what the issue is and where it lives (endpoint, page, file)
- steps or a minimal request that reproduces it
- the impact you expect

## What to expect

- An acknowledgement within 7 days.
- A fix or a clear decision within 30 days for confirmed issues, depending on severity.
- Credit in the fix commit if you would like it.

## Scope

In scope:

- the FastAPI backend (`backend/`): search, recommendation and comic detail endpoints
- XSS through comic synopses, titles or other text pulled from AniList, Metron or Wikipedia and rendered in the frontend
- unsafe loading of the bundled cache files (`catalog_cache.pkl`, `vector_cache.npy`)
- denial of service through very large or crafted search queries
- vulnerable dependencies

Out of scope: errors in third-party catalogue data, recommendation quality, and reports from automated scanners without a working proof of concept.

## Notes for self-hosting

- Keep the Metron credentials and any other secrets in environment variables. Never commit them.
- Only load pickle caches that you built yourself. A pickle file from an untrusted source can run code when loaded.
