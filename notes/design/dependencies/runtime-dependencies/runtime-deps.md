# Runtime Dependencies Analysis

## What Are Runtime Dependencies?
Runtime dependencies are packages required for the application to **run in production**.
They are listed under `"dependencies"` in `package.json` files, unlike `"devDependencies"`
which are only needed during development and testing.

## Techniques Used
- **Static analysis** — reading `package.json` files directly from the source code
- **Automated traversal** — recursive script that walks through all folders in the monorepo
- **Filtering** — only extracting `"dependencies"` and ignoring `"devDependencies"`

## Tools Used
- **Node.js** — to run the extraction script
- **Git** — to clone the Backstage repository
- **GitHub** — to store and share the results

## Methodology
To extract runtime dependencies from the Backstage monorepo:
1. Cloned the official Backstage repository from GitHub
2. Wrote an automated script (`extract-runtime.js`) that walks through all packages
3. For each `package.json` found, extracted only the `"dependencies"` section
4. Saved all results into `runtime-deps.json`

## Results
- **228 packages** were found with runtime dependencies
- The full dependency map is available in `runtime-deps.json`

## Key Observations

### Frontend Dependencies
Backstage frontend packages rely heavily on:
- **React ecosystem** (`react`, `react-dom`, `react-router-dom`)
- **Material UI** (`@material-ui/core`, `@material-ui/icons`)
- **Backstage core** (`@backstage/core-plugin-api`, `@backstage/core-components`)

### Backend Dependencies
Backstage backend packages rely on:
- **Express** for HTTP server
- **Knex** for database queries
- **Winston** for logging
- **Zod** for validation

### Shared Dependencies
Many packages share common dependencies:
- `lodash` - utility functions
- `luxon` - date/time handling
- `zod` - schema validation

## Conclusions
Backstage is a highly modular system with over 228 packages each having their own runtime dependencies. Key observations:
- The frontend heavily depends on **React** and **Material UI** for the UI layer
- The backend relies on **Express** for HTTP and **Knex** for database access
- **Zod** and **Lodash** appear across many packages showing they are core utilities
- Each plugin is independently deployable with its own isolated dependencies
- This modularity makes Backstage highly extensible and maintainable
