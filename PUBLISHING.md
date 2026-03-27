# Publishing Guide

Instructions for maintaining and releasing `book-producer`.

## Release targets

This repo now prepares and publishes two package variants:

- npm: `book-producer`
- GitHub Packages: `@<github-owner>/book-producer`

The npm package name stays unscoped. The GitHub Packages variant is generated from the same source tree with a scoped manifest during release preparation.

## Validation checklist

- `npm ci`
- `npm run build`
- `npm test`
- `npm run lint`
- `npm run prepare:publish:npm`
- `BOOK_PRODUCER_GITHUB_SCOPE=@<owner> npm run prepare:publish:github`
- `npm pack ./.release/npm`
- `npm pack ./.release/github`

## Local package preparation

### npm package

```bash
npm run prepare:publish:npm
npm pack ./.release/npm
```

### GitHub Packages variant

```bash
$env:BOOK_PRODUCER_GITHUB_SCOPE='@mrudinal'
npm run prepare:publish:github
npm pack ./.release/github
```

## GitHub Actions

The repo includes:

- `.github/workflows/ci.yml` for build, test, lint, and pack validation
- `.github/workflows/publish.yml` for npm and GitHub Packages publishing

### Required secrets

- `NPM_TOKEN` for npmjs.org publish
- `GITHUB_TOKEN` is used automatically for GitHub Packages publish

## Publish flow

1. Update docs and changelog.
2. Run the validation checklist locally.
3. Create a GitHub release or trigger the publish workflow manually.
4. The publish workflow:
   - validates the package
   - prepares `.release/npm`
   - publishes `book-producer` to npm
   - prepares `.release/github`
   - publishes `@<github-owner>/book-producer` to GitHub Packages

## Install commands for users

### npm

```bash
npm install -g book-producer
```

### GitHub Packages

```bash
npm install -g @<github-owner>/book-producer --registry=https://npm.pkg.github.com
```

## Notes

- `.book-framework/` is installed in the user's target repository, not in the global package install location.
- `.spec/<book-slug>/` is where book specs and workflow memory are written.
- Later numbered stage files are created lazily as the workflow advances.
