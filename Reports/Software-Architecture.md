# Software Architecture Report: Backstage

**System:** [Backstage](https://github.com/backstage/backstage)  
**C4 diagrams tool:** PlantUML with the C4-PlantUML standard library

---

## 1. Context Level

### Diagram

![Context Diagram](../../out/notes/architecture/diagrams/context-diagram/context-diagram.png)

### Explanation

Backstage is an internal developer portal framework — one place for engineering teams to discover services, read documentation, understand ownership, and create new projects from approved templates.

Three groups of people use the portal:

- **Developers** — primary users. Register services by adding `catalog-info.yaml` descriptors to their repositories, then browse the catalog, inspect metadata, read TechDocs, and scaffold new projects.
- **Platform Engineers** — set up and maintain the instance: configure plugins, connect integrations, manage authentication.
- **Engineering Managers** — mostly read-only: service ownership, team structure, ecosystem health.

Backstage depends on five external systems:

- **Source Control** (GitHub, GitLab) — Backstage reads `catalog-info.yaml` files and creates new repositories through Scaffolder templates.
- **CI/CD** (Jenkins, GitHub Actions) — build and deployment status, surfaced through dedicated frontend plugins and entity annotations; handled at the plugin layer, not by core Catalog.
- **Cloud Infrastructure** (Kubernetes, AWS, GCP) — queried for runtime and resource information related to services.
- **Identity Provider** (Okta, GitHub OAuth) — authenticates users and resolves group membership, mapped to `User` and `Group` catalog entities.
- **Object Storage** (AWS S3, GCS, Azure Blob) — stores generated TechDocs HTML assets when an external TechDocs publisher is configured.

---

## 2. Container Level

### Diagram

![Container Diagram](../../out/notes/architecture/diagrams/container-diagram/container-diagram.png)

### Explanation

- **Frontend SPA.** A React/TypeScript single-page application running in the browser. It is mainly a composition layer: it wires installed frontend plugins (Catalog UI, Scaffolder UI, TechDocs reader, Search) into one portal experience. Plugins share functionality through Backstage Utility APIs and link to each other through the routing system. The frontend reaches external systems only through the App Backend.
- **App Backend.** A Node.js/TypeScript runtime hosting backend plugins. A typical deployment runs several plugins in one process, but they stay logically isolated. The backend acts as composition root and dependency-injection container: it wires plugins, shared services (logging, configuration, database, cache), and plugin modules. Plugins coordinate through defined APIs rather than shared internals, which makes splitting them into separate backend deployments feasible later (with some configuration and operational changes).
- **PostgreSQL.** The main durable store in production deployments. Database access is scoped per plugin — separate plugin databases or isolated tables and migrations — which reduces coupling and stops one plugin's data model leaking into another.
- **Cache Store.** An optional Redis or Keyv-compatible cache; useful in production as a distributed cache, with a per-plugin namespace to avoid key collisions.
- **Object Storage.** Modeled as an external system because it is a managed third-party service. Backstage reads/writes generated TechDocs assets there but does not deploy it.

### Relationship With Clean Architecture

Backstage does not implement Clean Architecture in strict textbook form, but its design is broadly compatible: domain logic is kept away from infrastructure, dependencies flow inward toward stable abstractions, and concrete infrastructure is wired in at the outermost composition layer.

| Clean Architecture Layer | Backstage Equivalent |
| --- | --- |
| **Entities** | Shared domain packages such as `catalog-model`, defining entity types (`Component`, `API`, `User`, `Group`…) with no dependency on Express, PostgreSQL, Redis, or any frontend framework. |
| **Use Cases** | Application-level backend plugin logic: Catalog ingestion, entity processing, validation, stitching, and Scaffolder task orchestration (template + parameters → fetch/transform/publish → scaffolded repo). |
| **Interface Adapters** | REST route handlers in backend plugins, the `catalog-client` package translating HTTP responses into typed domain objects, frontend API clients, and React presenter components. |
| **Frameworks and Drivers** | The `app/` and `backend/` composition roots, Express routing, Knex database access, Keyv cache, identity providers, source-control integrations. |

Dependencies follow the Clean Architecture rule at the package level. `catalog-client` is a clear Dependency Inversion case — consumers depend on the `CatalogApi` interface, not on Catalog internals — and the backend system resolves typed service references at the composition root. Plugins sharing one process still share logger, database, cache, scheduler, and configuration through the DI container, but as abstractions, so inversion still holds with a service interface (rather than a separate process) as the boundary. Boundary discipline — only typed domain data crossing boundaries, never raw database rows — is enforced by package boundaries, `@internal` annotations, and code review rather than one universal compile-time rule.

---

## 3. Component Level

### 3.1 Container Selection and Scope

Level 3 zooms inside a container. This report expands two true Level 2 containers — the **App Backend** and the **Frontend SPA** — plus a deeper deep-dive on the **Catalog Plugin**, which is a component view *inside* the App Backend, not a separate container. The App Backend is expanded because ingestion, scaffolding, authentication, search, permissions, and most integration behaviour live there. The Catalog Plugin earns its own view because every major feature depends on catalog metadata, and its provider/processor/stitching pipeline illustrates the core Backstage patterns better than any other plugin. The Frontend SPA is expanded because it has its own plugin system, dependency-inversion mechanism, routing, and isolation rules that mirror the backend.

### 3.2 App Backend Components

#### Diagram

![App Backend Component Diagram](../../out/notes/architecture/diagrams/component-diagram-backend/component-diagram-backend.svg)

#### Explanation

The view shows the Backend System / DI Container, six core backend plugins, and one optional CI/CD integration. In the default deployment these share one process but stay separate plugin boundaries.

| Component | Role |
| --- | --- |
| **Backend System / DI Container** | Hands each registered plugin the services it declared — database, logger, cache, config, scheduler, discovery — so no plugin constructs concrete infrastructure itself. |
| **Catalog Plugin** | Ingests `catalog-info.yaml`, runs the processing pipeline, resolves relations, stitches entities, exposes the Catalog REST API. Consumed externally via the `CatalogApi` interface. |
| **Scaffolder Plugin** | Turns each request into an async task: fetch template → transform with user input → create repository → publish. Persists task state and logs; can check permissions before sensitive actions. |
| **Auth Plugin** | Sign-in flows per identity provider. The `SignInResolver` maps an external identity to a Backstage user and catalog entity; OAuth providers act as adapters behind one contract. |
| **TechDocs Plugin** | Docs-as-code. Local setup: generates docs via MkDocs. Production: CI generates, Backstage serves static assets from object storage. |
| **Search Plugin** | Background collators build search documents from Catalog/TechDocs; a REST endpoint queries the engine — Lunr, PostgreSQL, or Elasticsearch/OpenSearch — behind a `SearchEngine` interface. |
| **Permission Plugin** | Evaluates access-control policies and returns allow/deny. Backend plugins must still enforce server-side; frontend checks are UX only, not a security boundary. |
| **CI/CD Integration / Proxy** | Optional. Dedicated plugins or proxy routes fetch build/deploy status (Jenkins, GitHub Actions, Buildkite…) via entity annotations — not a Catalog responsibility. |

**Cross-plugin communication.** Plugins depend on API contracts (e.g. `CatalogApi`), never on each other's internals — keeping each a separate boundary and making a later split into independent deployments feasible.

### 3.3 Catalog Plugin Components

#### Diagram

![Catalog Plugin Component Diagram](../../out/notes/architecture/diagrams/component-diagram-catalog-plugin/component-diagram-catalog-plugin.svg)

#### Explanation

This view zooms inside the Catalog Plugin — a component view within the App Backend, not a separate container.

| Component | Role |
| --- | --- |
| **CatalogRouter** | Public REST API for catalog operations (list, fetch by reference, register locations, validate). Interface adapter: translates HTTP into calls on catalog services. |
| **CatalogBuilder** | Plugin-level composition root. Registers entity providers, processors, policies, and the processing engine at startup; assembles extension points. |
| **EntityProvider** | Adapters for entity sources (GitHub, GitLab, LDAP, static location). Feed raw entity data in without the catalog knowing provider specifics. |
| **RefreshStateStore** | Tracks refresh state of raw entities and locations — what to process, when to retry, which errors occurred. |
| **CatalogProcessingEngine** | Coordinates the processing loop: claims due entities, applies processors, stores emitted relations/errors, triggers stitching. |
| **EntityProcessor** | Validates, enriches, and transforms raw entities; emits relations, errors, derived entities. Ports-and-Adapters: interchangeable extension points around a stable pipeline. |
| **StitchingOrchestrator** | Assembles the final visible entity from processed data, relations, errors, and referenced entities. Entities are exposed only once fully stitched. |
| **EntitiesCatalog** | Read/write facade over the entity store, hiding database access behind a catalog-specific interface. |
| **CatalogClient / CatalogApi** | Public API boundary for external consumers. Frontend and other plugins depend on this, not on internals — the clearest Dependency Inversion case in the diagram. |

### 3.4 Frontend SPA Components

#### Diagram

![Frontend Component Diagram](../../out/notes/architecture/diagrams/component-diagram-frontend/component-diagram-frontend.svg)

#### Explanation

The Frontend SPA is itself a composition runtime: it assembles frontend plugins into one portal rather than holding all UI logic directly.

| Component | Role |
| --- | --- |
| **App Shell** | Frontend composition root. Mounts top-level routes, provides theme/layout, registers plugins, builds the sidebar and the API provider. |
| **ApiRegistry / Utility APIs** | Frontend dependency injection. Plugins request APIs via `useApi(apiRef)` instead of constructing clients, so implementations can be swapped without touching UI code. |
| **Auth / Identity UI** | Sign-in page and OAuth redirect flow. Exposes identity and tokens so plugin clients call backend APIs on the user's behalf. |
| **Catalog UI Plugin** | Catalog index and entity detail pages. Fetches via `CatalogApi`; uses entity-aware layouts (`EntitySwitch`) to render a different view per entity kind. |
| **Scaffolder UI Plugin** | Template list, parameter wizard, task progress. Calls the Scaffolder backend via `ScaffolderApi` and streams task logs. |
| **TechDocs UI Plugin** | Documentation index and reader. Links catalog entities to docs and fetches rendered static assets from the TechDocs backend. |
| **Search UI Plugin** | Search page, modal, bar, and result list. Other plugins can contribute custom result renderers — another composition point. |
| **Permission Framework** | Hooks and components (`usePermission`, `RequirePermission`) to hide UI actions. UX only — backend enforcement is still required. |
| **Core Component Library** | Reusable presentation components (tables, headers, sidebars, progress, empty states). Shared UI infrastructure, not business logic. |

### 3.5 SOLID Violations

The catalog ingestion pipeline (`plugins/catalog-backend`) — providers, processors, processing engine, stitcher, database access — contains the most significant SOLID violations in the system. **OCP, LSP, and DIP are respected**: new providers/processors are added via extension points without core edits; processors honour the optional-method contract; and engine/orchestrator dependencies are all constructor-injected as abstractions.

| Principle | Status | Notes |
| --- | --- | --- |
| **SRP** | Violated (high) | `DefaultCatalogProcessingEngine` — file 510 LOC, class itself ~330 — mixes pipeline lifecycle, per-task orchestration, hash-based change detection, cache-TTL bookkeeping, orphan cleanup, error-event publishing, and observability (tracing + metrics). Six-plus distinct reasons to change. A maintainer comment in the file itself notes the engine area is historically tangled. |
| **SRP** | Minor smell | `DefaultCatalogProcessingOrchestrator` (464 LOC) sequences the five-stage processor pipeline — its legitimate single job. Genuinely separable concerns (output collection, processor cache) are already delegated to `ProcessorOutputCollector` and `ProcessorCacheManager`. Residual smell: inline entity validation and catalog-rules enforcement could be uniform pluggable steps. Not a god class. |
| **ISP** | Violated | `CatalogProcessor` (`plugin-catalog-node`) bundles four separable lifecycle roles — `readLocation`, `preProcessEntity`, `validateEntityKind`, `postProcessEntity` — plus `getProcessorName`/`getPriority` in one type. All lifecycle hooks are optional, so the orchestrator must feature-detect each at runtime (`if (processor.preProcessEntity)` …) — proof that clients depend on a broader type than they use. |

---

## 4. Architectural Characteristics

Backstage's **driving characteristic is extensibility**; the others serve it or are constraints accepted to reach it.

| Characteristic | How the architecture supports it | Trade-off / limit |
| --- | --- | --- |
| **Extensibility / Modifiability** | Plugin boundaries (each feature = own package, routes, DB scope); extension points (typed hooks — no forking); DI via `ServiceRef` / `ApiRef` (depend on interfaces, swap implementations) | High learning curve; many packages to govern |
| **Testability** | Falls out of DI — no plugin imports a concrete dependency, so mocks inject through the same `ServiceRef` / `ApiRef` used in production | — |
| **Scalability** | Stateless backend (no in-memory sessions, no local disk writes) → horizontal scaling is a replica-count change, no code change | Plugins can't scale independently in the single-process default |
| **Maintainability** | Yarn/Lerna monorepo — one lockfile, one toolchain (`@backstage/cli`); cross-plugin refactors atomic | CI cost across 100+ packages |
| **Fault isolation** | Plugin-scoped DB connections, no shared mutable state — one plugin's data fault can't corrupt another | Single process: an unhandled crash still drops all plugins |
| **Deployability** | HTTP-only inter-plugin communication via runtime discovery → plugins splittable into separate deployments later | Split needs startup-order / config / ownership changes |

**Net:** the architecture genuinely supports its driving characteristic; the recurring cost is the single-process default trading per-plugin independence for operational simplicity.

---

## 5. Conclusion

Backstage's defining decision is that plugin boundaries are the product. It accepts the cost of dependency injection, API contracts, extension points, and plugin-scoped persistence so an organization can assemble a portal from independently evolving features.

The central trade-off is centralization versus independence. The Catalog is the shared semantic hub that makes the portal coherent — but that same centrality makes catalog data quality a system-wide dependency: weak annotations or ownership data degrade Search, TechDocs, and Permissions alike.

The architecture already provides the right mechanisms; the main risk is internal discipline. The `catalog-backend` ingestion pipeline shows this clearly — clean, tool-enforced *external* boundaries can still hide oversized *internal* components. Improvement effort belongs there: stricter API contracts and tighter components, not a different container structure.
