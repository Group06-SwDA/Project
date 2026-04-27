# Project Activity Log: Backstage

## Author: Stefano Alverino

### 2026-04-09

- Created and initialized the poject repository.

- Forked the Backstage repository to create a snapshot.

### 2026-04-10

- Team meeting: decided to spend the first week reading the documentation and understanding the codebase.

### 2026-04-12

- Started reviewing the Backstage documentation.

### 2026-04-15
- Took some notes on the documentation.
- Continued reviewing the documentation.

### 2026-04-16

- Finished high level doc review

### 2026-04-17

- Meeting to review document notes taken by the entire team and to divide subtasks
- Began organizing the design working group
- Researched tools for commit scraping to analyze knowledge dependencies

### 2026-04-19

- Researched the best approach to extract data from git history
- Designed the overall analysis pipeline
- Implemented commit extraction and generated the raw dataset

### 2026-04-20

- Designed the data filtering strategy
- Implemented filters to remove noise (merge commits, bots, non-code files)

### 2026-04-21

- Designed and implemented co-change analysis between files
- Designed and implemented author coupling analysis

### 2026-04-22

- Designed and built the knowledge dependency graph
- Applied Louvain clustering (chosen for scalability and ability to detect communities in large graphs)
- Generated the final diagram
- Started validating the correctness of the extracted data (ongoing)