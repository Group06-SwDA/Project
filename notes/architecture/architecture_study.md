# Project Activity Log: Backstage

## Author: Giuseppe Calvello

### ./docs/contribute/project-structure.md

Into this file I found the actual project structure.
The project follows a monorepo setup ( is a version control strategy where code for multiple distinct projects, applications, or services—such as frontend, backend, and shared libraries—is hosted in a single repository). It is about code organization, not architecture.
There's a section in which it is defined the content of the various packages that build the entire system.
For the analysis of the architecture is important to watch the backend/ folder, that for definition in docs is said that "The backend uses plugins to construct a working backend that the frontend (app) can use." From this we can extrapulate that the system follows a Plugin architecture or a plugin architecture.
Before doing a code inspection I've started reading in ./docs/architecture-decisions/ the records about architectural decisions:
There are 14 actually different records, mostly they are about coding conventions, not structural decisions.
The ADRs relevant to our report are:

##  Context level (C4-L1)

### ADR002 Default Catalog File Format

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

###  ADR011 — Plugin Package Structure

- This record provides rules for naming plugin packages. Plugins are named x, with the option of having a related backend plugin called x-backend (where x is the plugin name, like catalog or techdocs). There is a need for sharing code between the frontend and backend of a plugin, between backend plugins, or components and hooks between different frontend plugins . This results in emerging plugin packages with shared code, like packages/catalog-client or packages/techdocs-common.
To follow this necessity the decision that has been taken is:
"We will place all plugin related code in the plugins/ directory. The packages/ directory is reserved for core package of Backstage.

We follow this structure for plugin packages (where x is the plugin name, for example catalog or techdocs):

- x: Contains the main frontend code of the plugin.
- x-module-<name>: Contains optional modules related to the frontend plugin package.
- x-backend: Contains the main backend code of the plugin.
- x-backend-module-<name>: Contains optional modules related to the backend plugin package.
- x-react: Contains shared widgets, hooks and similar that both the plugin itself (x) and third-party frontend plugins can depend on.
- x-node: Contains utilities for backends that both the plugin backend itself (x-backend) and third-party backend plugins can depend on.
- x-common: An isomorphic package with platform agnostic models, clients, and utilities that all packages above or any third-party plugin package can depend on.
We prefix the package names with @backstage/plugin-."

- Each plugin = own npm package = container boundary
- Structure: src/index.ts, src/plugin.ts, src/api.ts, src/components/ — reveals container internals
- Frontend plugin vs backend plugin split → two deployment units

### ADR004 — Module Export Structure

- Public API surface defined per package → explicit container interface
- @internal annotation = what leaks vs what is stable contract

---

## Clean Architecture Relationship

ADR004 + ADR011 together reveal:

Entities layer      → catalog-model (pure domain types)
Use Cases layer     → plugin business logic (e.g. catalog-backend)
Interface Adapters  → plugin API clients (e.g. catalog-client)
Frameworks layer    → app/ + backend/ composition roots

ADR003 (avoid default exports) → enforces explicit dependency naming → supports dependency inversion

## SOLID at Component Level

| ADR | SOLID Principle | Description |
| :--- | :--- | :--- |
| ADR003 — named exports | **SRP**: Single Responsibility Principle | Each export = one responsibility, easy to see |
| ADR004 — module boundaries | **ISP**: Interface Segregation Principle | Consumers import only what they need |
| ADR011 — plugin structure | **OCP**: Open/Closed Principle | Extend via new plugin, not modify core |
| ADR009 — entity references | **LSP**: Liskov Substitution Principle | All entities share EntityRef contract |

---

## Architectural Characteristics

###  ADR009 - Entity References

Defines how entities are referred. The textual format, as written by humans, to reference entities by name is on the following form, where square brackets denote optionality:

[<kind>:][<namespace>/]<name>
That is, it is composed of between one and three parts in this specific order, without any additional encoding, with those exact separator characters. Optionality of kind and namespace are contextual, and they may or may not have default contextual fallback values.

When that format is insufficient or when machine made interchange formats wish to express such relations in a more expressive form, a nested structure on the following form can be used:

kind: <kind>
namespace: <namespace>
name: <name>
Important finding: Backstage ADRs are mostly **coding conventions**, not structural decisions. Map them honestly to report sections:

---

**ADR005** — Catalog Core Entities
- Standardized model → **interoperability** across org
- `metadata.annotations` = escape hatch for **evolvability**

**ADR014** — HTTP fetching
- Standardized fetch usage → **observability**, consistent error handling across containers

---

## Critical Gap: What ADRs DON'T Cover

Most architectural decisions live *outside* ADR folder. 

**Bottom line:** ADR005 + ADR009 + ADR011 are the three most architectural ADRs. Rest are style decisions useful only for SOLID section (OCP, ISP, SRP evidence).