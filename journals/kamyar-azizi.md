# Project Activity Log: Backstage

## Author: Kamyar Azizi

### 2026-04-09

- Initialized `kamyar-azizi.md` for project tracking.

### 2026-04-10

- Team meeting: decided on reading the documentation and understanding the code base for the first week

### 2026-04-12

- Started reading the documentation

### 2026-04-14

- Analyzed the Software Cataloge feature

### 2026-04-16

- Drafted a concise summary of the Backstage system
- Deployed a local instance of Backstage to explore its core functionalities

### 2026-04-17

- Team meeting: discussed the overall project scope and divided tasks among team members. I was assigned to analyze the design aspects of the system.
- Began reviewing the project’s data dependencies at the package level

### 2026-04-19

- Conducted an analysis of the project’s package dependencies and documented their structure and relationships.
- Created the Package Dependencies file

### 2026-04-20

- Initiated research into automated approaches for analyzing large-scale codebases, focusing on tools and methods to efficiently extract dependency information.

### 2026-04-21

- Developed a concise summary of the package dependencies to support a clearer understanding of the system architecture.
- Created a personal working branch to manage and push changes.

- #### Module Dependency Analysis

- Performed circular dependency analysis across the repository using Madge:

```bash
npx madge --extensions ts,tsx --circular .
```

- Identified circular dependency chains across multiple packages, highlighting areas of tight coupling within the codebase.
- Conducted module-level dependency extraction for the main application package:

```bash
npx madge packages/app/src --json > module-dependencies.json
```

- Exported the resulting module dependency graph into a structured JSON file (module-dependencies.json) for further analysis and documentation purposes.
- Pushed existing files to my personal branch and merged the branch into main.

### 2026-04-23

- Had a short team meeting to check everyone’s progress and what they were working on.

### 2026-04-25

- Developed a script named `extract-structural` to extract structural dependencies from the codebase.
- Generated `structural-deps.json`, containing the extracted structural dependency data.

### 2026-04-26

- Developed a script to transform the structural dependency JSON into a format compatible with Mermaid diagrams.

### 2026-04-27

- Identified that the full structural dependency graph was too large and complex (~500 relationships) to be used directly for visualization.
- Developed a second script to summarize and abstract the structural dependencies into higher-level architectural groups.

### 2026-04-29

- Created UML diagrams for package dependencies using PlantUML.
- Used Mermaid for structural dependency diagrams due to better readability for larger graphs.

### 2026-04-30

- Finalized diagrams and supporting files for inclusion in project documentation.
- Created a Design Notes document (`kamyar-azizi-note.md`) containing the work I have done on dependency analysis, including package, module, and structural dependencies, along with explanations for other team members.

### 2026-05-07

- Held a meeting with the team to review the progress made by others, discuss the next steps, and exchange knowledge across the team.

### 2026-05-11

- Started reviewing other team members’ work and became more involved in understanding the architecture side of the project.
