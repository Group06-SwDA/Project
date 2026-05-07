# Runtime Dependencies Analysis Notes

## 📦 Runtime Dependency Analysis Overview
The runtime dependency analysis aimed to understand which external packages are 
necessary for Backstage to run in production, to identify the key libraries each 
package depends on, and to outline the system's production needs clearly.

## 🔍 What Are Runtime Dependencies?
Runtime dependencies are packages listed under `"dependencies"` in each `package.json` 
file. Unlike `"devDependencies"`, these packages are needed for the application to 
work in production, not just during development or testing.

## 🛠️ Methodology

### Extraction Script
I created a custom script `extract-runtime.js` to automatically gather runtime 
dependencies from all packages in the Backstage monorepo.

The script functions by:
- Cloning the official Backstage repository from GitHub
- Scanning all folders in the monorepo for `package.json` files
- For each `package.json` found, extracting only the `"dependencies"` section
- Avoiding `node_modules` directories to prevent false results
- Compiling the results into a structured format (`package name → runtime dependencies`)

The result of this process is a file named `runtime-deps.json`, which contains 
the runtime dependencies for all 228 packages identified in the monorepo.

### Running the Script
```bash
node extract-runtime.js
```

## 📊 Results
- **Total packages analyzed:** 228
- **Output file:** `runtime-deps.json`

## 🧠 Key Observations

### Frontend Dependencies
Backstage frontend packages depend significantly on:
- **React ecosystem** (`react`, `react-dom`, `react-router-dom`)
- **Material UI** (`@material-ui/core`, `@material-ui/icons`)
- **Backstage core** (`@backstage/core-plugin-api`, `@backstage/core-components`)

### Backend Dependencies
Backstage backend packages rely on:
- **Express** for the HTTP server
- **Knex** for database queries
- **Winston** for logging
- **Zod** for validation

### Shared Dependencies
Several packages share common utilities:
- `lodash` — utility functions
- `luxon` — date/time handling
- `zod` — schema validation

## ✅ Conclusions
Backstage is a modular system with 228 packages, each managing its own runtime 
dependencies. The frontend depends heavily on React and Material UI, while the 
backend is built around Express and Knex. Common utilities like Zod and Lodash 
are used across many packages, highlighting their importance as foundational 
libraries in the Backstage ecosystem.
