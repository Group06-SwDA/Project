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
