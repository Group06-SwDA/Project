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

Backstage does not implement Clean Architecture in a strict textbook form, but many of its design choices follow the same general idea: important domain concepts and plugin logic are kept away from infrastructure details where possible.

| Clean Architecture Layer | Backstage Equivalent |
|---|---|
| **Entities** | Shared domain models such as `catalog-model`, which defines catalog entity types like `Component`, `API`, `Resource`, `User`, `Group`, `System`, and `Domain`. These models do not depend on Express, PostgreSQL, or frontend frameworks. |
| **Use Cases** | Backend plugin logic, such as Catalog ingestion, entity stitching, validation, and Scaffolder template execution. |
| **Interface Adapters** | REST route handlers in backend plugins, plugin API clients such as `catalog-client`, and React components that present backend data to users. |
| **Frameworks and Drivers** | The `app/` and `backend/` composition roots, Express routing, Knex database access, Redis/Keyv cache integration, and other concrete infrastructure choices. |

The dependency direction generally follows the Clean Architecture dependency rule. Core model packages, such as `catalog-model`, do not know about Express, PostgreSQL, or Redis. Backend plugin logic can use those models, while the concrete infrastructure is connected at the outer layers through services and the backend composition root. Backstage also reinforces package boundaries through conventions such as `@internal` annotations, which mark implementation details that should not be imported across package boundaries.

Overall, the architecture supports modularity by separating the portal into frontend plugins, backend plugins, shared services, and external integrations. This lets organizations extend Backstage without changing the whole system every time they add a new capability.
