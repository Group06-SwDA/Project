# Software Architecture Report: Backstage

**System:** [Backstage](https://github.com/backstage/backstage)  
**C4 diagrams tool:** PlantUML with the C4-PlantUML standard library

---

## 1. Context Level

### Diagram

![Context Diagram](../../out/notes/architecture/diagrams/context-diagram/context-diagram.png)

### Explanation

Backstage is an internal developer portal framework originally created by Spotify and now hosted by the Cloud Native Computing Foundation (CNCF). Its main goal is to give engineering teams one place to discover services, read documentation, understand ownership, and create new projects from approved templates. In this way, Backstage reduces the amount of scattered knowledge that developers normally have to collect from many different tools.

At the context level, Backstage is the central system used by three main groups of people.

**Developers** are the primary users of the portal. They register services by adding `catalog-info.yaml` descriptor files to their repositories, then use Backstage to browse the software catalog, inspect service metadata, read TechDocs, and scaffold new projects.

**Platform Engineers** are responsible for setting up and maintaining the Backstage instance. They configure plugins, connect external integrations, manage authentication, and adapt the portal to the needs of the organization.

**Engineering Managers** mostly use Backstage in a read-only way. They use it to understand service ownership, team structures, and the general health of the engineering ecosystem.

Backstage also depends on several external systems. Source Control, such as GitHub or GitLab, is one of the most important dependencies because Backstage reads `catalog-info.yaml` files from repositories and can also create new repositories through scaffolder templates. CI/CD systems, such as Jenkins or GitHub Actions, provide build and deployment status that can be displayed in the catalog. Cloud Infrastructure, such as Kubernetes, AWS, or GCP, is queried so that teams can see runtime and resource information related to their services. Finally, an Identity Provider, such as Okta or GitHub OAuth, authenticates users and resolves group membership, which Backstage maps to `User` and `Group` catalog entities.

---

## 2. Container Level

### Diagram

![Container Diagram](../../out/notes/architecture/diagrams/container-diagram/container-diagram.png)

### Explanation

At the container level, Backstage is mainly organized around a **Frontend SPA**, an **App Backend**, a **PostgreSQL database**, and an optional **Redis cache**.

**Frontend SPA.** The frontend is a React and TypeScript single-page application that runs in the user's browser. It brings together all installed frontend plugins, such as the Catalog UI, Scaffolder UI, TechDocs reader, Kubernetes dashboard, and Search. The application itself works mostly as a composition layer: it wires plugin extensions into one portal experience. Frontend plugins can share functionality through Backstage Utility APIs and can link to each other through the Backstage routing system. The frontend communicates with external systems through the App Backend instead of calling those systems directly.

**App Backend.** The backend is a Node.js and TypeScript runtime that hosts Backstage backend plugins. In a typical deployment, several backend plugins run inside the same backend process, but they are still designed to remain logically isolated. The backend application mainly acts as a composition root and dependency injection container: it wires together plugins, shared services such as logging and configuration, database access, and plugin modules. Each backend plugin exposes its own APIs and owns its own responsibilities. When plugins need to coordinate, for example when Search indexes Catalog entities, they should interact through defined APIs rather than by sharing internal implementation details. This design also makes it possible to split plugins into separate backend deployments when stronger isolation or independent scaling is needed.

**PostgreSQL.** PostgreSQL is the main durable data store for Backstage. Backend plugins keep their data isolated by using separate logical schemas and independent migrations. This reduces coupling between plugins and helps prevent one plugin's data model from leaking into another plugin.

**Redis Cache Store.** Redis is optional for local development, but it is useful in production as a distributed cache. Backstage plugins use a Keyv-compatible cache client, and each plugin can use its own namespace to avoid key collisions.

**Object Storage.** Object storage is modeled as an external system because it is normally provided by a managed third-party service, such as AWS S3, Google Cloud Storage, or Azure Blob Storage. Backstage integrates with it, for example to read or write generated TechDocs assets, but it is not deployed as part of the Backstage application itself.

### Relationship With Clean Architecture

Backstage does not implement Clean Architecture in strict textbook form, but its design is broadly compatible with its core principles: domain logic is kept away from infrastructure, dependencies flow inward toward stable abstractions, and concrete infrastructure is wired in at the outermost composition layer.

### Layer Mapping

| Clean Architecture Layer | Backstage Equivalent |
|---|---|
| **Entities** | Shared domain packages such as `catalog-model`, defining entity types (`Component`, `API`, `User`, `Group`, etc.) with no dependency on Express, PostgreSQL, Redis, or any frontend framework. |
| **Use Cases** | Application-level backend plugin logic: Catalog ingestion, entity processing, validation, stitching, and Scaffolder task orchestration. The Scaffolder is a concrete example — it takes a template and user parameters as input, orchestrates fetch/transform/publish steps, and produces a scaffolded repository as output. |
| **Interface Adapters** | REST route handlers in backend plugins, the `catalog-client` package (translates HTTP responses into typed domain objects), frontend API clients, and React presenter components. |
| **Frameworks and Drivers** | The `app/` and `backend/` composition roots, Express routing, Knex database access, Redis/Keyv cache integration, identity providers, source-control integrations, and all other concrete infrastructure. |

### Dependency Rule and Dependency Inversion

The dependency direction follows the Clean Architecture rule at the package level. The `catalog-client` is a clear application of Dependency Inversion: consumers depend on the `CatalogApi` interface, not on Catalog internals, decoupling them from the plugin's implementation and deployment topology. The new backend system formalises this through typed service references resolved at the composition root, keeping dependencies pointing inward. Cross-plugin communication is expected to happen over the network rather than through direct code imports, enforcing a hard boundary between plugins.

One nuance: plugins sharing the same backend process do share services (logger, database, cache) through the DI container. These are provided as abstractions, so the inversion principle still applies, but the boundary is a service interface rather than a network call.

### Boundary Crossing and Ports and Adapters

Clean Architecture requires that only data shaped for the inner layer crosses a boundary — never raw database rows or internal objects. In well-structured areas, such as the Catalog, this holds: `catalog-client` wraps responses in typed `Entity` objects defined by the shared domain model. In older or less mature plugins, database-level structures are sometimes more visible than they should be. Boundary discipline is enforced by convention (`@internal` annotations, code review) rather than by hard compile-time constraints.

Backstage also aligns with the Ports and Adapters pattern through its swappable infrastructure: the Keyv cache abstraction hides whether Redis or in-memory storage is used; the `SignInResolver` interface decouples identity logic from the choice of provider (Okta, GitHub OAuth, etc.); and TechDocs storage adapters work interchangeably across AWS S3, GCS, and Azure. This allows infrastructure decisions to be deferred or changed without touching plugin logic.

### Testability

Plugin isolation supports testability: core logic can be exercised using mock implementations of the logger, database, and cache provided by Backstage's testing utilities. However, some route handlers mix HTTP plumbing with business logic rather than delegating to a thin, independently testable layer — the Humble Object pattern Clean Architecture recommends. Boundary discipline here is inconsistent across the codebase.

### Overall Assessment

Backstage's strongest Clean Architecture alignments are its inward dependency direction, interface-based cross-plugin communication, and swappable infrastructure adapters. Its weakest areas are inconsistent boundary crossing discipline in older plugins and the absence of a uniform Humble Object separation in route handlers. Overall, it is best described as a system that produces the practical benefits Clean Architecture aims for — modular, independently extendable plugins — through its own conventions rather than through strict textbook adherence.
