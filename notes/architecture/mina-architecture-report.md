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

Backstage also depends on several external systems. Source Control, such as GitHub or GitLab, is one of the most important dependencies because Backstage reads `catalog-info.yaml` files from repositories and can also create new repositories through scaffolder templates. CI/CD systems, such as Jenkins or GitHub Actions, provide build and deployment status that can be displayed in the catalog. Cloud Infrastructure, such as Kubernetes, AWS, or GCP, is queried so that teams can see runtime and resource information related to their services. An Identity Provider, such as Okta or GitHub OAuth, authenticates users and resolves group membership, which Backstage maps to `User` and `Group` catalog entities. Object Storage, such as AWS S3, Google Cloud Storage, or Azure Blob Storage, can store generated TechDocs HTML assets when an external TechDocs publisher is configured.

---

## 2. Container Level

### Diagram

![Container Diagram](../../out/notes/architecture/diagrams/container-diagram/container-diagram.png)

### Explanation

At the container level, Backstage is mainly organized around a **Frontend SPA**, an **App Backend**, a durable **database**, an optional **cache store**, and external systems such as source control, identity providers, cloud infrastructure, CI/CD systems, and object storage.

**Frontend SPA.** The frontend is a React and TypeScript single-page application that runs in the user's browser. It brings together all installed frontend plugins, such as the Catalog UI, Scaffolder UI, TechDocs reader, Kubernetes dashboard, and Search. The application itself works mostly as a composition layer: it wires plugin extensions into one portal experience. Frontend plugins can share functionality through Backstage Utility APIs and can link to each other through the Backstage routing system. The frontend communicates with external systems through the App Backend instead of calling those systems directly.

**App Backend.** The backend is a Node.js and TypeScript runtime that hosts Backstage backend plugins. In a typical deployment, several backend plugins run inside the same backend process, but they are still designed to remain logically isolated. The backend application mainly acts as a composition root and dependency injection container: it wires together plugins, shared services such as logging and configuration, database access, cache access, and plugin modules. Each backend plugin exposes its own APIs and owns its own responsibilities. When plugins need to coordinate, for example when Search indexes Catalog entities, they should interact through defined APIs rather than by sharing internal implementation details. This design also makes it possible to split plugins into separate backend deployments when stronger isolation or independent scaling is needed.

**PostgreSQL.** PostgreSQL is the main durable data store in common production Backstage deployments. Backstage scopes database access per plugin, commonly through separate plugin databases or isolated tables and migrations depending on configuration. This reduces coupling between plugins and helps prevent one plugin's data model from leaking into another plugin.

**Cache Store.** Redis or another Keyv-compatible cache is optional for local development, but it is useful in production as a distributed cache. Each plugin can use its own namespace to avoid key collisions.

**Object Storage.** Object storage is modeled as an external system because it is normally provided by a managed third-party service, such as AWS S3, Google Cloud Storage, or Azure Blob Storage. Backstage integrates with it to read or write generated TechDocs assets, but it is not deployed as part of the Backstage application itself. In a basic TechDocs setup, the backend may generate and store docs locally; in the recommended production setup, CI/CD generates the documentation and Backstage serves the static files from external storage.

### Relationship With Clean Architecture

Backstage does not implement Clean Architecture in strict textbook form, but its design is broadly compatible with its core principles: domain logic is kept away from infrastructure, dependencies flow inward toward stable abstractions, and concrete infrastructure is wired in at the outermost composition layer.

### Layer Mapping

| Clean Architecture Layer | Backstage Equivalent |
|---|---|
| **Entities** | Shared domain packages such as `catalog-model`, defining entity types (`Component`, `API`, `User`, `Group`, etc.) with no dependency on Express, PostgreSQL, Redis, or any frontend framework. |
| **Use Cases** | Application-level backend plugin logic: Catalog ingestion, entity processing, validation, stitching, and Scaffolder task orchestration. The Scaffolder is a concrete example: it takes a template and user parameters as input, orchestrates fetch/transform/publish steps, and produces a scaffolded repository as output. |
| **Interface Adapters** | REST route handlers in backend plugins, the `catalog-client` package that translates HTTP responses into typed domain objects, frontend API clients, and React presenter components. |
| **Frameworks and Drivers** | The `app/` and `backend/` composition roots, Express routing, Knex database access, Redis/Keyv cache integration, identity providers, source-control integrations, and all other concrete infrastructure. |

### Dependency Rule and Dependency Inversion

The dependency direction follows the Clean Architecture rule at the package level. The `catalog-client` is a clear application of Dependency Inversion: consumers depend on the `CatalogApi` interface, not on Catalog internals, decoupling them from the plugin's implementation and deployment topology. The new backend system formalizes this through typed service references resolved at the composition root, keeping dependencies pointed toward stable abstractions. Cross-plugin communication is expected to happen over APIs rather than through direct imports of another plugin's implementation, enforcing a hard logical boundary between plugins.

One nuance is that plugins sharing the same backend process do share services such as logger, database, cache, scheduler, and configuration through the dependency injection container. These are provided as abstractions, so the inversion principle still applies, but the boundary is a service interface rather than a fully separate process.

### Boundary Crossing and Ports and Adapters

Clean Architecture requires that only data shaped for the inner layer crosses a boundary, never raw database rows or internal objects. In well-structured areas, such as the Catalog, this holds: `catalog-client` wraps responses in typed `Entity` objects defined by the shared domain model. In older or less mature plugins, database-level structures can be more visible than they should be. Boundary discipline is enforced by convention, package boundaries, `@internal` annotations, and code review rather than by one universal compile-time rule.

Backstage also aligns with the Ports and Adapters pattern through its swappable infrastructure: the Keyv cache abstraction hides whether Redis or in-memory storage is used; the `SignInResolver` interface decouples identity logic from the choice of provider such as Okta or GitHub OAuth; and TechDocs storage adapters work interchangeably across AWS S3, GCS, Azure, or local filesystem storage. This allows infrastructure decisions to be deferred or changed without touching plugin logic.

### Testability

Plugin isolation supports testability: core logic can be exercised using mock implementations of the logger, database, cache, and other services provided by Backstage's testing utilities. However, some route handlers mix HTTP plumbing with business logic rather than delegating to a thin, independently testable layer, which is the Humble Object pattern that Clean Architecture recommends. Boundary discipline is therefore strong in some areas, such as the Catalog, but inconsistent across the whole ecosystem.

---

## 3. Component Level

### 3.1 Container Selection and Scope

At Level 3, the goal is to zoom inside a single container and show what is actually running inside it. In this report, two true Level 2 containers are expanded: the **App Backend** and the **Frontend SPA**. The **Catalog Plugin** also gets a separate deep-dive because it is the most central backend plugin, but it should be understood as an internal component view inside the App Backend, not as a separate container from the Level 2 diagram.

The **App Backend** is the obvious first choice. This is where ingestion, scaffolding, authentication, search, permissions, and most cross-system integration behaviour live.

The **Catalog Plugin** gets its own deep-dive because it sits at the centre of the developer portal. Every other major feature depends on catalog metadata in some way, and its provider/processor/stitching pipeline illustrates the core patterns used across Backstage better than any other single plugin.

The **Frontend SPA** is included because Backstage is not just a simple frontend over a backend API. The frontend has its own plugin system, dependency inversion mechanism, routing system, and isolation rules that mirror the backend.

**PostgreSQL, the Cache Store, and Object Storage are intentionally left out as component diagrams.** They are infrastructure containers with no application components of their own in this analysis. Their architectural role is already captured at the Container level: plugin-scoped persistence, namespaced caching, and external TechDocs asset storage.

---

### 3.2 App Backend Components

#### Diagram

![App Backend Component Diagram](../../out/notes/architecture/diagrams/component-diagram-backend/component-diagram-backend.svg)

#### Explanation

The App Backend runs seven major components inside a Node.js backend deployment: a **Backend System / DI Container** that wires everything together, and six backend plugins: **Catalog**, **Scaffolder**, **Auth**, **TechDocs**, **Search**, and **Permission**. In the default deployment these are hosted in one backend process, but architecturally they remain separate plugin boundaries.

**Backend System / DI Container.** Implemented around Backstage's backend system APIs, its job is to take every registered plugin and hand it the services it declared it needs: a database connection, logger, cache client, configuration reader, scheduler, discovery service, and so on. No plugin needs to construct these concrete services directly. This keeps infrastructure wiring in one place and lets plugins depend on service interfaces.

**Catalog Plugin.** The Catalog Plugin ingests entity descriptors, most commonly `catalog-info.yaml` files from source control. It runs them through a processing pipeline, resolves relationships between entities, stitches final entity records, stores them in the catalog database scope, and exposes the Catalog REST API. Other plugins should not depend on its internal implementation; they use the `CatalogApi` interface through `CatalogClient`.

**Scaffolder Plugin.** Each scaffolding request becomes an asynchronous task. A worker executes a chain of actions such as fetching template files, transforming them with user input, creating a repository in source control, and publishing the result. Task state and logs are persisted so the frontend can display progress. Before running sensitive actions, the Scaffolder can check permissions.

**Auth Plugin.** The Auth Plugin handles sign-in flows for configured identity providers. Its important design point is the `SignInResolver`, which maps an external identity, such as a GitHub user or Okta account, to a Backstage user identity and catalog entity. Provider-specific OAuth implementations act as adapters behind the same conceptual contract.

**TechDocs Plugin.** The TechDocs backend supports documentation-as-code. In basic local setups it can prepare, generate, and publish docs itself using MkDocs. In recommended production deployments, CI/CD generates the static documentation and publishes it to object storage, while Backstage mainly serves and transforms those assets for the TechDocs reader.

**Search Plugin.** Search has two separate jobs. In the background, collators fetch content from sources such as Catalog and TechDocs and build search documents. At request time, a REST endpoint queries the configured search engine. Backstage supports an in-memory Lunr engine for simple development usage, PostgreSQL for deployments that want to avoid another external service, and Elasticsearch/OpenSearch for larger production setups. The engine sits behind a `SearchEngine` interface.

**Permission Plugin.** The Permission Plugin evaluates access-control policies registered by platform engineers. Other plugins ask it for allow or deny decisions, and backend plugins must still enforce those decisions server-side. The frontend permission framework is useful for hiding UI actions, but it is not a security boundary.

**Cross-plugin communication.** Backend plugins are treated as independent features. When Search, Scaffolder, or Permission needs catalog data, they should depend on the Catalog API contract rather than importing Catalog internals. This keeps plugin boundaries clear and makes it possible to move plugins into separate backend deployments later.

---

### 3.3 Catalog Plugin Components

#### Diagram

![Catalog Plugin Component Diagram](../../out/notes/architecture/diagrams/component-diagram-catalog-plugin/component-diagram-catalog-plugin.svg)

#### Explanation

The Catalog Plugin component diagram zooms into the most important backend plugin. It is not a separate Level 2 container; it is a deeper component view inside the App Backend.

**CatalogRouter** exposes the public REST API for catalog operations, such as listing entities, fetching entities by reference, registering locations, and validating entities. It should be treated as an interface adapter: it translates HTTP requests into calls on catalog application services.

**CatalogBuilder** acts as the plugin-level composition root. It registers entity providers, processors, policies, and the processing engine during startup. This is where the plugin's extension points are assembled.

**EntityProvider** implementations are adapters for external or configured entity sources. A GitHub provider, GitLab provider, LDAP provider, or static-location provider can each feed raw entity data into the catalog without the rest of the catalog knowing the provider-specific details.

**RefreshStateStore** tracks the refresh state of raw entities and locations. It records what needs to be processed, when it should be retried, and which errors occurred during ingestion or processing.

**CatalogProcessingEngine** coordinates the processing loop. It claims entities that are due for processing, applies the registered entity processors, stores emitted data such as relations and errors, and triggers stitching.

**EntityProcessor** implementations validate, enrich, and transform raw entities. They can emit relations, errors, and derived entities. This is a strong Ports and Adapters example: processors are interchangeable extension points around a stable catalog pipeline.

**StitchingOrchestrator** assembles the final visible entity from processed data, relations, errors, and referenced entities. An entity is not exposed through the Catalog API until it has reached the final stitched state.

**EntitiesCatalog** is the read/write facade over the catalog entity store. It hides database access behind a catalog-specific interface so API handlers and processors do not need to work directly with raw database rows.

**CatalogClient / CatalogApi** is the public API boundary for consumers outside the plugin. Frontend code and other backend plugins depend on this API rather than reaching into Catalog internals. This is the clearest Dependency Inversion example in the diagram.

---

### 3.4 Frontend SPA Components

#### Diagram

![Frontend Component Diagram](../../out/notes/architecture/diagrams/component-diagram-frontend/component-diagram-frontend.svg)

#### Explanation

The Frontend SPA is also a composition runtime. It does not contain all user-facing functionality directly; instead, it assembles frontend plugins into one coherent portal experience.

**App Shell** is the frontend composition root. It mounts top-level routes, provides theme and layout, registers installed plugins, sets up the sidebar, and creates the API provider used by plugin components.

**ApiRegistry / Utility APIs** is the frontend equivalent of dependency injection. Plugins ask for APIs through `useApi(apiRef)` rather than constructing concrete clients directly. This lets the app replace or customize implementations without changing plugin UI code.

**Auth / Identity UI** handles the sign-in page and OAuth redirect flow. After sign-in, it exposes identity information and tokens through the frontend identity APIs so plugin clients can call backend APIs on behalf of the user.

**Catalog UI Plugin** provides the catalog index page and entity detail pages. It fetches data through `CatalogApi` and uses entity-aware layouts such as `EntitySwitch` to render different views for components, APIs, templates, groups, users, and other entity kinds.

**Scaffolder UI Plugin** provides the software template list, parameter wizard, and task progress view. It calls the Scaffolder backend through `ScaffolderApi` and streams task logs back to the user.

**TechDocs UI Plugin** provides documentation index and reader views. It connects catalog entities to generated documentation and fetches rendered static assets through the TechDocs backend.

**Search UI Plugin** provides search surfaces such as the search page, search modal, search bar, and result list. Other plugins can contribute custom result renderers, which is another example of frontend plugin composition.

**Permission Framework** provides hooks and components such as `usePermission` and `RequirePermission` to hide or show UI actions. This improves user experience, but backend plugins still need to enforce permissions because frontend checks can be bypassed.

**Core Component Library** provides reusable presentation components such as tables, headers, sidebars, progress indicators, and empty states. It is shared UI infrastructure rather than business logic.

---

## 4. Conclusion

Backstage is best understood as a plugin-based developer portal framework with strong logical boundaries. At the Context level, it is a central portal connecting developers, platform engineers, managers, and external engineering systems. At the Container level, it is mainly a React frontend, a Node.js backend, plugin-scoped persistence, optional cache infrastructure, and external integrations. At the Component level, its architecture is shaped by plugin composition, dependency injection, API boundaries, and extension points.

The architecture is not a pure textbook Clean Architecture implementation, but it uses many compatible ideas: stable domain models, explicit plugin APIs, dependency inversion through service references and API refs, and infrastructure adapters that can be swapped through configuration. The Catalog Plugin is the strongest example because its provider, processor, storage, stitching, and client boundaries clearly show how Backstage separates external inputs, application processing, persistence, and public API access.
