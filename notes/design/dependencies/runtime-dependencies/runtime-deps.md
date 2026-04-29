# Runtime Dependencies Analysis

## What Are Runtime Dependencies?
Runtime dependencies are packages required for the application to **run in production**.
They are listed under `"dependencies"` in `package.json` files, unlike `"devDependencies"`
which are only needed during development and testing.

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
