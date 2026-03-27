# Package Publishing Guide

Instructions for publishing `book-producer` manually from a local machine.

This package is published to two targets from the same source:

- **npm registry** — unscoped: `book-producer`
- **GitHub Packages** — scoped: `@<github-username>/book-producer`

---

## Prerequisites

### npm account

You need an npm account with publish rights to the `book-producer` package.

```bash
npm login
# Username: rudinmax87 (example — use your own npm username)
# Password: <your npm password>
# Email: <your email>
```

Verify you are logged in:

```bash
npm whoami
# rudinmax87
```

### GitHub Packages authentication

GitHub Packages requires a Personal Access Token (PAT) with `write:packages` scope.

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate a new token with scopes: `write:packages`, `read:packages`, `repo`
3. Add it to your `.npmrc` (in your home directory, not the project):

```
//npm.pkg.github.com/:_authToken=YOUR_GITHUB_PAT
@mrudinal:registry=https://npm.pkg.github.com
```

Replace `mrudinal` with your GitHub username.

---

## Validation checklist

Run these before every publish:

```bash
npm ci
npm run build
npm test
npm run lint
npm audit --omit=dev
npm pack --dry-run
```

All must pass with no errors.

---

## Publishing to npm

### 1. Prepare the npm release artifact

```bash
npm run prepare:publish:npm
```

This populates `.release/npm/` with the correct package manifest.

### 2. Pack and inspect (optional but recommended)

```bash
npm pack ./.release/npm
```

Inspect the generated `.tgz` to confirm all files are present before publishing.

### 3. Publish to npm

```bash
npm publish ./.release/npm --access public
```

Verify on npm after publishing:

```bash
npm view book-producer
```

### Quick reference — npm publish (all steps, copy-paste)

```bash
npm ci
npm run build
npm test
npm run lint
npm audit --omit=dev
npm pack --dry-run
npm run prepare:publish:npm
npm pack ./.release/npm
npm publish ./.release/npm --access public
npm view book-producer
```

---

## Publishing to GitHub Packages

### 1. Set your GitHub scope

On Linux/macOS:

```bash
export BOOK_PRODUCER_GITHUB_SCOPE='@mrudinal'
```

On Windows (PowerShell):

```powershell
$env:BOOK_PRODUCER_GITHUB_SCOPE='@mrudinal'
```

Replace `@mrudinal` with your own `@<github-username>`.

### 2. Prepare the GitHub Packages release artifact

```bash
npm run prepare:publish:github
```

This populates `.release/github/` with the scoped package manifest (`@mrudinal/book-producer`).

### 3. Pack and inspect (optional but recommended)

```bash
npm pack ./.release/github
```

### 4. Publish to GitHub Packages

```bash
npm publish ./.release/github --registry=https://npm.pkg.github.com
```

Verify on GitHub after publishing:

Go to your GitHub profile → Packages → `book-producer`

### Quick reference — GitHub Packages publish (all steps, copy-paste)

```bash
npm ci
npm run build
npm test
npm run lint
npm audit --omit=dev
npm pack --dry-run
export BOOK_PRODUCER_GITHUB_SCOPE='@mrudinal'
npm run prepare:publish:github
npm pack ./.release/github
npm publish ./.release/github --registry=https://npm.pkg.github.com
```

---

## Version bump workflow

Before publishing a new version:

1. Update the version in `package.json`
2. Add an entry to `CHANGELOG.md`
3. Update `VERSIONS.md` if needed
4. Commit: `git commit -m "chore: bump version to X.Y.Z"`
5. Tag the release: `git tag vX.Y.Z`
6. Push: `git push && git push --tags`
7. Run the validation checklist
8. Publish to npm
9. Publish to GitHub Packages

---

## Install commands for end users

After publishing, users install with:

```bash
# From npm
npm install -g book-producer

# From GitHub Packages (replace <github-username> with the publisher's GitHub username)
npm install -g @mrudinal/book-producer --registry=https://npm.pkg.github.com
```

---

## Troubleshooting

**`403 Forbidden` on npm publish**
- Run `npm whoami` to confirm you are logged in
- Confirm the package name is not claimed by another account
- For scoped packages, pass `--access public`

**`401 Unauthorized` on GitHub Packages publish**
- Confirm your PAT has `write:packages` scope
- Confirm the `_authToken` line in `~/.npmrc` is correct
- Confirm the `@<scope>:registry` line points to `https://npm.pkg.github.com`

**Wrong files in the package**
- Run `npm pack --dry-run` and inspect the file list
- Check the `files` field in `package.json`
- Rebuild with `npm run build` before preparing the release
