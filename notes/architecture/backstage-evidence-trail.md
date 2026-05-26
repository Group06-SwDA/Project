# Architecture Evidence Trail — Backstage

**Purpose:** For every claim in `backstage-architecture-analysis.md`, this file records the exact source file, URL, and code snippet where the evidence was found.

---

## Context Level Evidence

### "Backstage is a developer portal platform"
- **Source:** `docs/architecture-decisions/adr002-default-catalog-file-format.md`
- **URL:** `https://raw.githubusercontent.com/backstage/backstage/master/docs/architecture-decisions/adr002-default-catalog-file-format.md`
- **Evidence:** ADR describes the catalog as the central registry of all software components in an org, with YAML descriptor files committed alongside source code.

### Entity taxonomy (Component, API, Resource, User, Group, System, Domain, Location)
- **Source:** `packages/catalog-model/src/kinds/` — one file per kind
- **URL prefix:** `https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/kinds/`
- **Evidence (ComponentEntity):**
  ```typescript
  export interface ComponentEntityV1alpha1 extends Entity {
    apiVersion: 'backstage.io/v1alpha1' | 'backstage.io/v1beta1';
    kind: 'Component';
    spec: {
      type: string;
      lifecycle: string;
      owner: string;
      providesApis?: string[];
      consumesApis?: string[];
      dependsOn?: string[];
      system?: string;
    };
  }
  ```
- **ADR reference:** `docs/architecture-decisions/adr005-catalog-core-entities.md` — formally records the decision to use these three foundational kinds.

---

## Container Level Evidence

### "Monorepo, Yarn workspaces, plugin = npm package"
- **Source:** `plugins/catalog/package.json`
- **URL:** `https://raw.githubusercontent.com/backstage/backstage/master/plugins/catalog/package.json`
- **Evidence:**
  ```json
  {
    "name": "@backstage/plugin-catalog",
    "backstage": { "role": "frontend-plugin", "pluginId": "catalog" }
  }
  ```
- **Source:** `plugins/catalog-backend/package.json`
- **Evidence:**
  ```json
  {
    "name": "@backstage/plugin-catalog-backend",
    "backstage": { "role": "backend-plugin", "pluginId": "catalog" }
  }
  ```
- **Source:** `packages/catalog-model/package.json`
- **Evidence:**
  ```json
  {
    "name": "@backstage/catalog-model",
    "backstage": { "role": "common-library" }
  }
  ```

### "URL-based Service Discovery"
- **Source:** `packages/backend-plugin-api/src/services/definitions/coreServices.ts`
- **URL:** `https://raw.githubusercontent.com/backstage/backstage/master/packages/backend-plugin-api/src/services/definitions/coreServices.ts`
- **Evidence:** `core.discovery` service ref with `DiscoveryService` interface:
  ```typescript
  export interface DiscoveryService {
    getBaseUrl(pluginId: string): Promise<string>;
    getExternalBaseUrl(pluginId: string): Promise<string>;
  }
  ```

### "Two-scope DI (root vs plugin)"
- **Source:** `packages/backend-plugin-api/src/services/definitions/coreServices.ts`
- **Evidence:** Service refs use `scope` field:
  ```
  core.rootConfig    → scope: 'root'   (process-wide singleton)
  core.rootLogger    → scope: 'root'
  core.rootLifecycle → scope: 'root'
  core.rootHealth    → scope: 'root'
  core.logger        → scope: 'plugin' (isolated per plugin)
  core.database      → scope: 'plugin'
  core.cache         → scope: 'plugin'
  core.scheduler     → scope: 'plugin'
  ```
  Full list: 21 service definitions covering auth, userInfo, httpAuth, permissions, permissionsRegistry, cache, database, rootConfig, httpRouter, rootHttpRouter, lifecycle, rootLifecycle, scheduler, logger, rootLogger, auditor, rootHealth, discovery, pluginMetadata, rootInstanceMetadata, urlReader.

### "Catalog Database accessed via Knex"
- **Source:** `plugins/catalog-backend/package.json`
- **Evidence:**
  ```json
  "dependencies": {
    "knex": "..."
  }
  ```
- **Source:** `packages/backend-plugin-api/src/services/definitions/coreServices.ts`
- **Evidence:** `DatabaseService` interface:
  ```typescript
  export interface DatabaseService {
    getClient(): Promise<Knex>;
    migrations?: { skip?: boolean };
  }
  ```

---

## Component Level Evidence

### "catalogPlugin (frontend) registers catalogApiRef"
- **Source:** `plugins/catalog/src/index.ts`
- **URL:** `https://raw.githubusercontent.com/backstage/backstage/master/plugins/catalog/src/index.ts`
- **Evidence:** Exports `catalogPlugin` as the plugin instance, plus `CatalogIndexPage`, `CatalogEntityPage`, `EntityLayout`, `EntitySwitch`, `CatalogTable`, `catalogTranslationRef`.

### "createPlugin + createApiFactory — frontend DI composition"
- **Source:** `packages/core-plugin-api/src/plugin/index.ts`
- **URL:** `https://raw.githubusercontent.com/backstage/backstage/master/packages/core-plugin-api/src/plugin/index.ts`
- **Evidence:** Exports `createPlugin`, `BackstagePlugin`, `PluginConfig`, `createApiFactory` (re-exported via barrel).

### "ApiRef<T> — DI token with phantom type"
- **Source:** `packages/frontend-plugin-api/src/apis/system/ApiRef.ts`
- **URL:** `https://raw.githubusercontent.com/backstage/backstage/master/packages/frontend-plugin-api/src/apis/system/ApiRef.ts`
- **Evidence:**
  ```typescript
  export type ApiRefConfig = { id: string };
  // createApiRef<T>() returns object with:
  // - id: string (runtime identifier)
  // - T: T       (phantom type — exists only at compile time)
  // - toString() → "apiRef{plugin.namespace.api}"
  ```

### "11+ narrow frontend API interfaces (ISP)"
- **Source:** `packages/core-plugin-api/src/apis/definitions/`
- **URL:** `https://raw.githubusercontent.com/backstage/backstage/master/packages/core-plugin-api/src/apis/definitions/`
- **Evidence:** Exports: `AlertApi`, `AnalyticsApi`, `AppThemeApi`, `ConfigApi`, `DiscoveryApi`, `ErrorApi`, `FeatureFlagsApi`, `FetchApi`, `IdentityApi`, `OAuthRequestApi`, `StorageApi`, and auth APIs — each a separate interface with one responsibility.

### "useApi hook — consumer-side DI"
- **Source:** `packages/core-plugin-api/src/apis/`
- **Evidence:** `useApi(ref: ApiRef<T>): T` and `useApiHolder(): ApiHolder` exported from the same module.

### "createBackendPlugin + createExtensionPoint — OCP"
- **Source:** `packages/backend-plugin-api/src/wiring/createBackendPlugin.ts`
- **URL:** `https://raw.githubusercontent.com/backstage/backstage/master/packages/backend-plugin-api/src/wiring/createBackendPlugin.ts`
- **Evidence:**
  ```typescript
  export function createBackendPlugin(options: CreateBackendPluginOptions): BackendFeature {
    function getRegistrations() {
      options.register({
        registerExtensionPoint(extOrOpts, impl?) { ... },
        registerInit(regInit) { ... }
      });
    }
    return { $$type: '@backstage/BackendFeature', version: 'v1', ... };
  }
  
  export function createExtensionPoint<T>(options): ExtensionPoint<T> {
    return {
      id: options.id,
      T: null as T,   // phantom type
      toString() { return `extensionPoint{${options.id}}`; },
      $$type: '@backstage/ExtensionPoint',
    };
  }
  ```
- **Source:** `packages/backend-plugin-api/src/index.ts`
- **Evidence:** Exports `createBackendPlugin`, `createBackendModule`, `createExtensionPoint`, `createServiceFactory`, `createServiceRef` from `./wiring`.

### "Chain of Responsibility — catalog processing pipeline"
- **Source:** `plugins/catalog-backend/src/index.ts`
- **URL:** `https://raw.githubusercontent.com/backstage/backstage/master/plugins/catalog-backend/src/index.ts`
- **Evidence:** Exported processors:
  ```
  AnnotateLocationEntityProcessor
  BuiltinKindsEntityProcessor
  CodeOwnersProcessor
  FileReaderProcessor
  PlaceholderProcessor
  UrlReaderProcessor
  AnnotateScmSlugEntityProcessor
  transformLegacyPolicyToProcessor
  ```
  All implement `CatalogProcessor` interface (Chain of Responsibility participants).

### "EntitySwitch — Strategy pattern in JSX"
- **Source:** `plugins/catalog/src/index.ts`
- **Evidence:** `EntitySwitch` exported as a named component. Used in entity pages to conditionally render based on entity `kind`/`spec.type`.

---

## Clean Architecture Evidence

### "catalog-model has zero framework dependencies"
- **Source:** `packages/catalog-model/package.json`
- **URL:** `https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/package.json`
- **Evidence:**
  ```json
  {
    "dependencies": {
      "@backstage/errors": "workspace:^",
      "@backstage/types": "workspace:^",
      "ajv": "^8.10.0",
      "ajv-errors": "^3.0.0",
      "lodash": "^4.17.21",
      "zod": "^3.x"
    }
  }
  ```
  No `react`, `express`, `knex`, `@material-ui`, `winston` — pure domain logic.

### "Entity.ts — Kubernetes-inspired open/closed model"
- **Source:** `packages/catalog-model/src/entity/Entity.ts`
- **URL:** `https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/entity/Entity.ts`
- **Evidence:**
  ```typescript
  export type Entity = {
    apiVersion: string;   // versioned discriminator
    kind: string;         // type discriminator
    metadata: EntityMeta; // closed: controlled fields
    spec?: JsonObject;    // open: any domain-specific content
    relations?: EntityRelation[]; // computed graph, not user-authored
  };
  
  export type EntityMeta = JsonObject & {
    uid?: string;     // server-generated globally unique id
    etag?: string;    // optimistic concurrency control
    name: string;
    namespace?: string;
    annotations?: Record<string, string>;  // arbitrary key-value escape hatch
    tags?: string[];
    links?: EntityLink[];
  };
  ```

### "plugin-catalog depends on catalog-model and catalog-client, NOT catalog-backend"
- **Source:** `plugins/catalog/package.json`
- **Evidence:**
  ```json
  "dependencies": {
    "@backstage/catalog-client": "workspace:^",
    "@backstage/catalog-model": "workspace:^",
    "@backstage/core-plugin-api": "workspace:^"
  }
  ```
  No `@backstage/plugin-catalog-backend` dependency — Clean Architecture frontend/backend separation enforced at package level.

### "core-plugin-api is a stability facade over frontend-plugin-api"
- **Source:** `packages/core-plugin-api/package.json`
- **Evidence:**
  ```json
  "dependencies": {
    "@backstage/frontend-plugin-api": "workspace:^",
    "@backstage/version-bridge": "workspace:^"
  }
  ```
- **Source:** `packages/core-plugin-api/src/index.ts`
- **Evidence:** Pure barrel file re-exporting from `./analytics`, `./apis`, `./app`, `./extensions`, `./icons`, `./plugin`, `./routing` — stability facade pattern.

---

## SOLID Evidence

### SRP — Each service one responsibility
- **Source:** `packages/backend-plugin-api/src/services/definitions/coreServices.ts`
- **Evidence:** 21 separately defined service interfaces, each exported as its own `createServiceRef`. See full list under "Two-scope DI" above.

### OCP — Extension points
- **Source:** `packages/backend-plugin-api/src/wiring/createBackendPlugin.ts`
- **Evidence:** `createExtensionPoint<T>` and `registerExtensionPoint` mechanism — see "createBackendPlugin" evidence above.

### LSP — Entity kind substitutability
- **Source:** `packages/catalog-model/src/kinds/*.ts`
- **Evidence:** All kind interfaces use TypeScript `extends Entity`:
  ```typescript
  export interface ComponentEntityV1alpha1 extends Entity { ... }
  export interface ApiEntityV1alpha1 extends Entity { ... }
  export interface ResourceEntityV1alpha1 extends Entity { ... }
  ```
  Any code accepting `Entity` accepts any kind — LSP holds structurally.

### ISP — Narrow interfaces, no god-bag
- **Source:** Frontend: `packages/core-plugin-api/src/apis/definitions/` (11+ ApiRef tokens)
- **Source:** Backend: `packages/backend-plugin-api/src/services/definitions/coreServices.ts` (21 service refs)
- **Evidence:** `registerInit({ deps: { logger: coreServices.logger, database: coreServices.database } })` — plugin declares only what it needs.

### DIP — No concrete class imports in plugins
- **Source:** `plugins/catalog/package.json` — depends on `catalog-client` (abstraction), not on implementation class
- **Source:** `packages/core-plugin-api/src/apis/system/ApiRef.ts` — `createApiFactory` pattern:
  ```typescript
  createApiFactory({
    api: catalogApiRef,          // abstract token
    deps: { discoveryApi, fetchApi },
    factory: deps => new CatalogClient(deps)  // concrete only here, in composition root
  })
  ```

### SRP minor violation — AuthService dual responsibility
- **Source:** `packages/backend-plugin-api/src/services/definitions/coreServices.ts`
- **Evidence:** `AuthService` interface combines:
  - `authenticate(token)` — verification (authentication)
  - `getPluginRequestToken(...)` — token issuance for inter-service calls
  - `getLimitedUserToken(...)` — scoped token generation
  Two concerns (verify + issue) in one interface.

---

## Architectural Characteristics Evidence

### Extensibility
- **Source:** `packages/backend-plugin-api/src/wiring/createBackendPlugin.ts` — `createExtensionPoint`
- **Source:** `packages/catalog-model/src/entity/Entity.ts` — `spec?: JsonObject`, `annotations?: Record<string,string>`
- **Source:** ADR011 — `plugin-x-backend-module-<name>` package naming convention for optional extensions

### Observability
- **Source:** `plugins/catalog-backend/package.json`
- **Evidence:**
  ```json
  "@opentelemetry/api": "^1.9.0"
  ```
  OpenTelemetry at infrastructure level, not application level.
- **Source:** `coreServices.ts` — `core.auditor` service for audit trail, `core.rootHealth` for health endpoints.

### Security
- **Source:** `packages/backend-plugin-api/src/services/definitions/coreServices.ts`
- **Evidence:** `AuthService` interface with full credential lifecycle:
  ```typescript
  export interface AuthService {
    authenticate(token: string, opts?: { allowLimitedAccess: boolean }): Promise<BackstageCredentials>;
    isPrincipal<T>(credentials, type): credentials is BackstageCredentials<T>;
    getOwnServiceCredentials(): Promise<BackstageCredentials<BackstageServicePrincipal>>;
    getPluginRequestToken(opts: { onBehalfOf; targetPluginId }): Promise<{ token: string }>;
    getLimitedUserToken(credentials): Promise<{ token: string; expiresAt: Date }>;
  }
  ```
- **Source:** `packages/backend-plugin-api/src/services/definitions/coreServices.ts`
- **Evidence:** `HttpRouterService`:
  ```typescript
  addAuthPolicy(policy: { path: string; allow: 'unauthenticated' | 'user-cookie' }): void;
  ```
  Per-route explicit auth policy declarations.

### Scalability
- **Source:** `coreServices.ts` — `core.scheduler` with `SchedulerService`:
  ```typescript
  export interface SchedulerService {
    scheduleTask(task: SchedulerServiceTaskScheduleDefinition & ...): Promise<void>;
    triggerTask(id: string): Promise<void>;
    cancelTask(id: string): Promise<void>;
    getScheduledTasks(): Promise<SchedulerServiceTaskDescriptor[]>;
  }
  ```
  Distributed task locking prevents duplicate processing across backend instances.

---

## ADR Quick Reference

| ADR | File | Key claim it supports |
|-----|------|-----------------------|
| ADR002 | `docs/architecture-decisions/adr002-default-catalog-file-format.md` | Kubernetes-inspired YAML model, entity versioning, annotations escape hatch |
| ADR004 | `docs/architecture-decisions/adr004-module-export-structure.md` | Module export discipline → maintainability, deterministic public API surfaces |
| ADR005 | `docs/architecture-decisions/adr005-catalog-core-entities.md` | Domain model taxonomy (Component, API, Resource), relationships as directed graph |
| ADR011 | `docs/architecture-decisions/adr011-plugin-package-structure.md` | Plugin package hierarchy, layer separation enforced by package naming |
