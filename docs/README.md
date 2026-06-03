# Website

This website is built using [Docusaurus](https://docusaurus.io/), a modern static website generator.

### Installation

```
$ yarn
```

### Local Development

```
$ yarn start
```

This command starts a local development server and opens up a browser window. Most changes are reflected live without having to restart the server.

### Build

```
$ yarn build
```

This command generates static content into the `build` directory and can be served using any static contents hosting service.

### Deployment of Docs

The recommended deployment flow is now:

1. Build the docs locally:

```
$ npm install
$ npm run build
```

2. Publish the contents of `build/` to a `gh-pages` branch.

If you still want to use Docusaurus's built-in branch deployment helper, you can also run:

```
$ GIT_USER=<Your GitHub username> npm run deploy
```

This pushes the built site to the `gh-pages` branch, which can then be served directly by GitHub Pages without GitHub Actions.
