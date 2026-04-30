# Design Notes

## 📦 Dependency Analysis Overview

The dependency analysis was performed to understand how different parts of the codebase interact, identify hidden coupling, and improve the overall clarity of the system.

## 🧩 Package Dependencies

I reviewed the package dependencies by analyzing the existing package.json files across the repository. No custom tooling or additional scripts were required for this step, as the dependency information is already explicitly defined in the project configuration.

## 📊 Module Dependencies

I performed the module dependency analysis using `Madge`, a static analysis tool for inspecting JavaScript/TypeScript projects and generating dependency graphs between files and modules.

I also generated two views of the dependency structure: a circular dependency analysis and a full module dependency graph. The difference between them is that circular dependency analysis focuses only on detecting dependency cycles (i.e., where modules depend on each other in a loop), while the full module dependency graph captures all relationships between modules in the project.

### Circular Dependency Analysis

A circular dependency analysis was carried out using Madge:

```bash
npx madge --extensions ts,tsx --circular .
```

This allowed me to identify cycles in the codebase where modules depend on each other in a loop. These cases are important because they indicate tight coupling between components.

### Full Module Dependency Graph

To gain a more complete understanding of the application structure, I generated a full module dependency graph for the main application package:

```bash
npx madge packages/app/src --json > module-dependencies.json
```

This step allowed me to move beyond isolated issues (like cycles) and capture the full dependency structure of the application in a machine-readable format.

## 🧠 Structural Dependencies

Because the raw module dependency data was too large and detailed to interpret directly, I took a custom approach to extract structural dependencies at a higher level of abstraction.

### Extraction Script

I developed a custom script extract-structural.js to traverse the repository and identify dependencies between major modules (plugins and packages), rather than individual files.

The script works by:

- Recursively scanning all `.ts` and `.tsx` files in the repository
- Determining which plugin or package each file belongs to (based on folder structure)
- Extracting import statements that reference other Backstage plugins
- Normalizing dependency names to remove suffixes such as `-react` or `-node`
- Aggregating dependencies into a structured format (`source → target`)

The result of this process is a file: `structural-deps.json`

which contains dependency relationships between high-level modules (e.g., `catalog --> search`), along with their frequency.

### Transformation to Diagram Format

To visualize the data, I created a script `????????????.js` to convert the JSON structure into a format compatible with Mermaid, a lightweight diagramming syntax that can be embedded in Markdown.

This script maps each dependency into a graph edge format:

```bash
A --> B
```

and generates an output in a format compatible with Mermaid, which I used with the online Mermaid editor to generate the UML diagram.

### Summary Graph Generation

Since the full graph remained too complex, I delevoped a second script called `???????.js` to produce a summarized version of the dependencies compatible with Mermaid.

This script applies manual grouping and abstraction by:

- mapping modules into broader architectural domains
- collapsing multiple low-level dependencies into higher-level relationships

The grouping logic was based on manual analysis of the system structure, allowing the diagram to reflect meaningful concepts rather than raw file-level connections.
