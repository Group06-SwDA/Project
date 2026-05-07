# Runtime Dependencies Analysis Notes

## 📦 Runtime Dependency Analysis Overview
The runtime dependency analysis was performed to understand which external packages 
are required for Backstage to run in production, identify the core libraries each 
package relies on, and provide a clear picture of the system's production dependencies.

## 🔍 What Are Runtime Dependencies?
Runtime dependencies are packages listed under `"dependencies"` in each `package.json` 
file. Unlike `"devDependencies"`, these are required for the application to function 
in production, not just during development or testing.

## 🛠️ Methodology

### Extraction Script
I developed a custom script `extract-runtime.js` to automatically collect runtime 
dependencies from all packages in the Backstage monorepo.

The script works by:
- Cloning the official Backstage repository from GitHub
- Recursively scanning all folders in the monorepo for `package.json` files
- For each `package.json` found, extracting only the `"dependencies"` section
- Skipping `node_modules` directories to avoid false results
- Aggregating the results into a structured format (`package name → runtime dependencies`)

The result of this process is a file: `runtime-deps.json`
which contains the runtime dependencies of all 228 packages found in the monorepo.

### Running the Script
```bash
node extract-runtime.js
```

## 📊 Results
- **Total packages analyzed:** 228
- **Output file:** `runtime-deps.json`

## 🧠 Key Observations

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
Many packages share common utilities:
- `lodash` - utility functions
- `luxon` - date/time handling
- `zod` - schema validation

## ✅ Conclusions
Backstage is a highly modular system with 228 packages each managing their own 
runtime dependencies. The frontend relies heavily on React and Material UI, while 
the backend is built around Express and Knex. Common utilities like Zod and Lodash 
appear across many packages, reflecting their role as foundational libraries in 
the Backstage ecosystem.
