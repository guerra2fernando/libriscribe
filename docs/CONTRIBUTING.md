# Contributing

## Development setup

```bash
npm ci
npm run build
npm test
npm run lint
```

## Release-sensitive validation

For packaging-sensitive changes, also run:

```bash
npm run prepare:publish:npm
BOOK_PRODUCER_GITHUB_SCOPE=@<owner> npm run prepare:publish:github
npm pack ./.release/npm
npm pack ./.release/github
```

## What to keep aligned

- package runtime code under `src/`
- installed framework assets under `assets/`
- tool adapter docs under `assets/tooling/`
- user-facing docs in `README.md`, `PUBLISHING.md`, and `docs/`
- release workflows under `.github/workflows/`

## Behavioral expectations

- `.book-framework/` is the installed framework package inside the user's repository.
- `.spec/<book-slug>/` stores book workflow memory and specs.
- Later numbered stage files are created lazily as stages start.
- Claude may emit parallel packets; the other supported tools must stay sequential.
