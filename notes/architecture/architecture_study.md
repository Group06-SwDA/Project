./docs/contribute/project-structure.md

Into this file I found the actual project structure.
The project follows a monorepo setup ( is a version control strategy where code for multiple distinct projects, applications, or services—such as frontend, backend, and shared libraries—is hosted in a single repository). It is about code organization, not architecture.
There's a section in which it is defined the content of the various packages that build the entire system.
For the analysis of the architecture is important to watch the backend/ folder, that for definition in docs is said that "The backend uses plugins to construct a working backend that the frontend (app) can use." From this we can extrapulate that the system follows a Plugin architecture or a plugin architecture.
Before doing a code inspection I've started reading in ./docs/architecture-decisions/ the records about architectural decisions: 
There are 14 actually different records, mostly they are about coding conventions, not structural decisions.
The ADRs relevant to our report are:
## Context level (C4-L1):
### ADR002 Default Catalog File Format:
   - In the ../adr002-default-catalog-file-format.md is defined the software catalog functionality to track all ht software components and more. It can be powered by data from various sources, and one of them that is included with the package is a custom database backed catalog. It has the ability to keep itself updated automatically based on the contents of little descriptor files in your version control system of choice. Developers create these files and maintain them side by side with their code, and the catalog system reacts accordingly. This ADR describes the default format of these descriptor files.
     - Explains what Backstage is: developer portal with Software Catalog as core
     - Shows external actors: teams/engineers who write catalog-info.yaml
     - Reveals integrations: SCM systems (GitHub, GitLab) as external systems

### ADR005 — Catalog Core Entities
- In this report we can find a standardization on some core entities tracked into the Backstage catalog, in order to build specific plugins around them.
Here we can find many important definition about the domain:
- **Components** are individual pieces of software, like a web site, backend service or data pipeline, etc.
A component can be tracked in source control, or use some existing open source or commercial software.
Component entities are typically defined in YAML descriptor files next to the code of the component.
- **APIs** are boundaries between different components. APIs form an abstraction that allows large software ecosystems to scale. Thus, APIs are a first class citizen in the Backstage model and the primary way to discover existing functionality in the ecosystem. APIs are implemented by components and make their boundaries explicit.  In any case, APIs exposed by components need to be in a known machine-readable format so we can build further tooling and analysis on top.

APIs are typically indexed from existing definitions in source control and thus wouldn't need their own descriptor files, but would be stored in the catalog.



- **Resources** are physical or virtual infrastructure needed to operate a component.
Resources are the infrastructure your software needs to operate at runtime like Bigtable databases, Pub/Sub topics, S3 buckets or CDNs. Modelling them together with components and APIs will allow us to visualize and create tooling around them in Backstage.

Resources are typically indexed from declarative definitions (e.g. Terraform, GCP Config Connector, AWS Cloud Formation) and/or inventories from cloud providers (e.g. GCP Asset Inventory) and thus wouldn't need their own descriptor files, but would be stored in the catalog.
    - Defines domain vocabulary: Component, API, User, Group, System, Domain, Resource
    - Critical for context diagram actors and system boundaries


## Container Level (C4-L2)
### ADR011 — Plugin Package Structure
- 
- Each plugin = own npm package = container boundary
- Structure: src/index.ts, src/plugin.ts, src/api.ts, src/components/ — reveals container internals
- Frontend plugin vs backend plugin split → two deployment units


### ADR004 — Module Export Structure
- Public API surface defined per package → explicit container interface
- @internal annotation = what leaks vs what is stable contract

