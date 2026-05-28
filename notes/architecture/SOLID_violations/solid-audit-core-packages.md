# SOLID Audit — Core Packages of Backstage

This report assesses adherence to the SOLID principles across ten core package
groups of the Backstage monorepo. 

For each group the report records, per principle:

- **S** — Single Responsibility
- **O** — Open/Closed
- **L** — Liskov Substitution
- **I** — Interface Segregation
- **D** — Dependency Inversion

A summary heat map and an actionable list of recommended refactors follow the
package-by-package section.

---

## 1. `packages/catalog-model`

The entity schema layer: `Entity`, `apiVersion`, `kind`, `metadata`, `spec`,
plus per-kind types (`ComponentEntityV1alpha1`, `UserEntityV1alpha1`, etc.) and
validators.

| Principle | Status | Notes |
|-----------|--------|-------|
| SRP | Respected | One file per kind under `src/kinds/`; one validator per kind under `src/validation/`; `EntityPolicies.ts` only defines composite builders. |
| OCP | Respected | New kinds are added as new files plus a validator registration; existing kinds remain untouched. The discriminator `apiVersion + kind` keeps the model open for extension. |
| LSP | Respected | `AllEntityPolicies` and `AnyEntityPolicy` both implement `EntityPolicy` and honour an identical contract — composite pattern over a shared interface. |
| ISP | Minor smell | `Entity` is effectively a super-union over all kind shapes; consumers must branch on `kind` to recover narrow types. Cohesive enough to be considered acceptable. |
| DIP | Respected | Pure type and validation layer with no infrastructure dependencies. |

**Code references**

- `Entity` union: `packages/catalog-model/src/entity/Entity.ts`
- Per-kind definitions: `packages/catalog-model/src/kinds/{Component,Group,User,Resource,System,Domain,Api,Location}EntityV1alpha1.ts`
- Per-kind validators: `packages/catalog-model/src/validation/entityKindSchemaValidator.ts`
- Composite policy classes: `packages/catalog-model/src/EntityPolicies.ts:21-71`

**Verdict — clean.** No real violations.

---

## 2. `packages/core-plugin-api` (legacy) vs `packages/frontend-plugin-api` (new)

Two generations of the frontend plugin model coexist. The legacy package
exposes `createPlugin` and `Extension`; the new package exposes blueprints and
extension points.

| Principle | `core-plugin-api` | `frontend-plugin-api` |
|-----------|-------------------|------------------------|
| SRP | Respected — `PluginImpl` is 79 LOC, one job: hold plugin config and expose extensions. | Respected — blueprints are split into focused files (`ApiBlueprint`, `PageBlueprint`, `NavItemBlueprint`, `SubPageBlueprint`, `AppRootElementBlueprint`, etc.). |
| OCP | Mild violation — the visitor call `plugin.provide(extension)` couples plugins to extensions: each `Extension.expose(plugin)` reaches back into the plugin to read state. | Respected — `createExtensionBlueprint`, `createExtensionDataRef`, `createExtensionInput`, `createFrontendModule` together implement OCP cleanly. |
| LSP | Respected. | Respected. |
| ISP | Respected — `BackstagePlugin` exposes a small surface (`getId`, `getApis`, `getFeatureFlags`, `routes`, `externalRoutes`, `provide`). | Respected — each blueprint is its own narrow interface. |
| DIP | Mild concern — `ApiRef` resolves by string id; the legacy `ApiFactory` couples concrete classes to the `ApiHolder` implementation. | Respected — type-safe service refs and extension data refs. |

**Code references**

- Visitor coupling (legacy): `packages/core-plugin-api/src/plugin/Plugin.tsx:57-59`
  (`provide(extension) { return extension.expose(this); }`).
- Legacy `BackstagePlugin` interface: `packages/core-plugin-api/src/plugin/types.ts`.
- Legacy `ApiRef` and `ApiFactory`: `packages/core-plugin-api/src/apis/system/ApiRef.ts`,
  `packages/core-plugin-api/src/apis/system/types.ts`.
- New blueprints: `packages/frontend-plugin-api/src/blueprints/{ApiBlueprint,PageBlueprint,NavItemBlueprint,SubPageBlueprint,AppRootElementBlueprint}.{ts,tsx}`.
- New wiring primitives: `packages/frontend-plugin-api/src/wiring/{createExtension,createExtensionBlueprint,createExtensionDataRef,createExtensionInput,createFrontendModule}.ts`.

**Verdict — the legacy package has documented OCP/DIP weaknesses; the new
package was deliberately designed to fix them. The migration is itself an
explicit, in-progress remediation.**

---

## 3. `plugins/catalog` + `plugins/catalog-react`

The frontend rendering layer for catalog entities.

| Principle | Status | Notes |
|-----------|--------|-------|
| SRP | Respected | Clear directory split: `apis/`, `components/`, `context/`, `hooks/`, `filters.ts`, `routes.ts`. |
| OCP | Respected | UI extension via `overridableComponents.ts`; new entity pickers and cards can be registered without modifying the plugin core. |
| LSP | Respected. | |
| ISP | Respected | The `CatalogApi` interface is focused on catalog read operations. |
| DIP | Respected | UI components depend on `CatalogApi` references rather than concrete clients. |

**Code references**

- `CatalogApi` reference: `plugins/catalog-react/src/api.ts`.
- Overridable UI surface: `plugins/catalog/src/overridableComponents.ts`,
  `plugins/catalog-react/src/overridableComponents.ts`.
- Component directories: `plugins/catalog/src/components/`,
  `plugins/catalog-react/src/components/`.

**Verdict — clean.**

---

## 4. `plugins/catalog-backend`

The ingestion pipeline: providers, processors, processing engine, stitcher,
database access. This package contains the most significant SOLID violations
in the audit.

| Principle | Status | Notes |
|-----------|--------|-------|
| SRP | **Violated** | `DefaultCatalogProcessingEngine` (510 LOC) mixes polling-loop control, the task pipeline, stitching coordination, orphan cleanup, hash-based change detection, OpenTelemetry tracing, event emission, metrics, error event publishing, and cache-TTL bookkeeping. Six or more distinct reasons to change. |
| SRP | **Violated** | `DefaultCatalogProcessingOrchestrator` (464 LOC) similarly bundles the processor pipeline, emit collection, processor cache wiring, relation accumulation, and entity validation. |
| OCP | Respected | New providers and processors are added by implementing `CatalogProcessor` / `EntityProvider` and registering them via the plugin extension points — no core edits required. |
| LSP | Respected | Concrete processors honour the optional-method contract of `CatalogProcessor`. |
| ISP | **Violated** | `CatalogProcessor` in `plugin-catalog-node` is a fat interface bundling four unrelated lifecycle roles in one type: `readLocation`, `preProcessEntity`, `validateEntityKind`, `postProcessEntity`, plus `getProcessorName` and `getPriority`. All hooks are optional, which mitigates the impact, but the underlying smell remains: a single class type expresses four separable extension points. |
| DIP | Respected | Every dependency of the engine and orchestrator is injected via constructor options (database, stitcher, scheduler, events, logger, metrics, etc.). |

**Code references**

- SRP — processing engine god class:
  `plugins/catalog-backend/src/processing/DefaultCatalogProcessingEngine.ts:61-510`.
  Concrete hot spots inside that file:
  - constructor and field bag: `:61-115`
  - polling loop and task pipeline: `:138-260`
  - hash-based change detection: `:218-252`
  - error event publishing: `:208-217`
  - orphan cleanup scheduler: see `startOrphanCleanup` (same file).
- SRP — processing orchestrator god class:
  `plugins/catalog-backend/src/processing/DefaultCatalogProcessingOrchestrator.ts:1-464`.
- Shared interfaces (engine, orchestrator):
  `plugins/catalog-backend/src/processing/types.ts:62-76`.
- ISP — fat `CatalogProcessor` interface:
  `plugins/catalog-node/src/api/processor.ts:25-111`
  (six optional roles: `getProcessorName`, `readLocation`, `preProcessEntity`,
  `validateEntityKind`, `postProcessEntity`, `getPriority`).
- Concrete processors implementing the fat interface (LSP fine, ISP affected):
  - `plugins/catalog-backend/src/processors/BuiltinKindsEntityProcessor.ts:60`
  - `plugins/catalog-backend/src/processors/AnnotateLocationEntityProcessor.ts:36`
  - `plugins/catalog-backend/src/processors/AnnotateScmSlugEntityProcessor.ts:36`
  - `plugins/catalog-backend/src/processors/CodeOwnersProcessor.ts:35`
  - `plugins/catalog-backend/src/processors/FileReaderProcessor.ts:31`
  - `plugins/catalog-backend/src/processors/UrlReaderProcessor.ts:45`
  - `plugins/catalog-backend/src/processors/PlaceholderProcessor.ts:43`
- Supporting subsystems (not violators, included for navigation):
  `plugins/catalog-backend/src/stitching/DefaultStitcher.ts`,
  `plugins/catalog-backend/src/processing/TaskPipeline.ts`,
  `plugins/catalog-backend/src/processing/ProcessorCacheManager.ts`.

**Verdict — high severity. The processing engine and orchestrator are
god-classes; the processor interface is fat.**

---

## 5. `packages/backend-plugin-api`

The DI system for backend plugins: `coreServices`, service refs, service
factories, plugin and module wiring, extension points.

| Principle | Status | Notes |
|-----------|--------|-------|
| SRP | Respected | One service definition per file under `src/services/definitions/` (`AuthService.ts`, `DatabaseService.ts`, `LoggerService.ts`, etc.). The `src/wiring/` folder is similarly split: `createBackendPlugin`, `createBackendModule`, `createExtensionPoint`, `createBackendFeatureLoader`. |
| OCP | Respected | Plugins + modules + extension points form a textbook OCP composition: behaviour extends via new modules without modifying existing plugins. |
| LSP | Respected | Service refs are type-only; any implementation satisfying the interface is substitutable. |
| ISP | Respected | The legacy `TokenManager` god-interface has been broken up into `AuthService`, `HttpAuthService`, `UserInfoService` — exactly an ISP-driven refactor. |
| DIP | Respected | All consumption is via `coreServices.X` references; no plugin instantiates its own infrastructure. |

**Code references**

- Per-service definitions:
  `packages/backend-plugin-api/src/services/definitions/{AuthService,HttpAuthService,UserInfoService,DatabaseService,LoggerService,CacheService,SchedulerService,PermissionsService,PermissionsRegistryService,ActionsService,ActionsRegistryService,LifecycleService,UrlReaderService,DiscoveryService,AuditorService,HttpRouterService,RootConfigService,RootLoggerService,RootHttpRouterService,RootLifecycleService,RootHealthService,PluginMetadataService,RootInstanceMetadataService}.ts`.
- Service-ref / factory primitives:
  `packages/backend-plugin-api/src/services/system/types.ts`
  (`createServiceRef`, `createServiceFactory`).
- Wiring primitives:
  `packages/backend-plugin-api/src/wiring/{createBackendPlugin,createBackendModule,createExtensionPoint,createBackendFeatureLoader}.ts`.

**Verdict — gold standard. This package is the SOLID exemplar of the
monorepo.**

---

## 6. `packages/backend-defaults`

The concrete implementations of the core services: cache manager, database
manager, HTTP router, logger, scheduler, etc.

| Principle | Status | Notes |
|-----------|--------|-------|
| SRP | Respected | One folder per service under `src/entrypoints/`; each contains a single service factory. |
| OCP | Respected | `CacheManager` selects backend by config (`redis` / `valkey` / `memcache` / in-memory); new stores plug in via Keyv adapters without modifying the manager. |
| LSP | Respected | All cache and database backends are substitutable behind their service interfaces. |
| ISP | Respected | Each entrypoint exports a single focused factory. |
| DIP | Respected | Concrete implementations are wired against the `coreServices` refs declared in `backend-plugin-api`. |

**Code references**

- Service factories (one folder each):
  `packages/backend-defaults/src/entrypoints/{auditor,auth,cache,database,discovery,httpAuth,httpRouter,lifecycle,logger,permissions,permissionsRegistry,rootConfig,rootHealth,rootHttpRouter,rootLifecycle,rootLogger,scheduler,urlReader,userInfo}/`.
- Cache backend selection by config:
  `packages/backend-defaults/src/entrypoints/cache/CacheManager.ts`
  (and `CacheClient.ts`); Keyv adapters used: `@keyv/redis`, `@keyv/valkey`,
  `@keyv/memcache`.
- HTTP router (Express under the hood):
  `packages/backend-defaults/src/entrypoints/rootHttpRouter/rootHttpRouterServiceFactory.ts:24`,
  `packages/backend-defaults/src/entrypoints/rootHttpRouter/DefaultRootHttpRouter.ts:18`.

**Verdict — clean.**

---

## 7. `plugins/scaffolder` (and `scaffolder-node`)

The template system: actions, steps, dry-run, task runner.

| Principle | Status | Notes |
|-----------|--------|-------|
| SRP | Respected | `TemplateAction` is a focused record: `{ id, description, examples, supportsDryRun, schema, handler }`. Each action implements a single handler. |
| OCP | Respected | New actions are added via `createTemplateAction({...})` and registered through the extension point; templates compose actions declaratively. |
| LSP | Respected | All actions are interchangeable via the shared `ActionContext<TInput, TOutput>`. |
| ISP | Minor smell | `ActionContext` carries roughly twelve fields (`logger`, `secrets`, `workspacePath`, `input`, `checkpoint`, `output`, `createTemporaryDirectory`, `getInitiatorCredentials`, `task`, `templateInfo`, `isDryRun`, `user`, `signal`, `each`, `step`). It is conceptually one "per-action execution scope," but a typical action uses only a subset. |
| DIP | Respected | Handlers receive their context and do not construct their own dependencies. |

**Code references**

- `TemplateAction` type: `plugins/scaffolder-node/src/actions/types.ts:112-129`.
- `ActionContext` bag (~12 fields): `plugins/scaffolder-node/src/actions/types.ts:32-110`.
- Action factory: `plugins/scaffolder-node/src/actions/createTemplateAction.ts`.
- Extension point and registration: `plugins/scaffolder-node/src/extensions.ts`.
- Frontend extension surface: `plugins/scaffolder/src/extensions/default.ts`,
  `plugins/scaffolder/src/components/`.

**Verdict — clean; minor `ActionContext` bloat.**

---

## 8. `plugins/auth-backend` + `plugins/auth-backend-module-github-provider`

OAuth sign-in, identity resolution, token issuance, OIDC surface.

### Plugin (`plugins/auth-backend`)

| File | LOC | SRP grade | Note |
|------|-----|-----------|------|
| `authPlugin.ts` | 126 | A | DI wiring and extension-point registration only. |
| `database/*.ts` | — | A | One concern per database class. |
| `identity/{TokenFactory, StaticTokenIssuer, KeyStores, *KeyStore}.ts` | — | A | One strategy per file. |
| `service/CimdClient.ts`, `OfflineAccessService.ts`, `readTokenExpiration.ts` | — | A | Single concerns. |
| `actions/createWhoAmIAction.ts` | — | A | Single action. |
| `service/router.ts` | 179 | **C** | `createRouter` reads config, picks the token-issuer strategy, builds three databases, wires cookie/session/passport middleware, registers body parsers, binds provider routes, mounts the OIDC router and installs a catch-all 404 — five-plus reasons to change. |
| `providers/router.ts` | 159 | B | Bundles `bindProviderRouters` (provider routing) and `createOriginFilter` (CORS), two unrelated exports. |
| `service/OidcService.ts` | 655 | **C** | Mixes redirect-URI validation, CIMD metadata fetch usage, JWT decoding, OIDC database access via `OidcDatabase`, token issuance and offline-access integration. |
| `service/OidcRouter.ts` | 582 | B | Large but a single OIDC HTTP surface; could be split per endpoint group. |

| Principle | Status |
|-----------|--------|
| SRP | **Violated** at `service/router.ts` and `OidcService.ts`; otherwise respected. |
| OCP | Respected — `authProvidersExtensionPoint` and `authOwnershipResolutionExtensionPoint` allow modules to register providers and resolvers without modifying the plugin. |
| LSP | Respected. |
| ISP | Respected — provider, resolver, and token-issuer interfaces are narrow. |
| DIP | Respected. |

### Module (`auth-backend-module-github-provider`)

Source split into `authenticator.ts`, `resolvers.ts`, `module.ts` plus tests.
Each file has a single concern. **All five principles respected.**

**Code references**

- DI / extension-point composition root (clean):
  `plugins/auth-backend/src/authPlugin.ts:38-126`
  (extension points registered at `:44-62`, init at `:64-124`).
- SRP — composition god-function in `createRouter`:
  `plugins/auth-backend/src/service/router.ts:61-179`. Specific concerns inside:
  - token-issuer strategy selection: `:95-117`
  - cookie / session / passport middleware wiring: `:119-140`
  - body parsers: `:142-143`
  - provider routing call: `:145-153`
  - OIDC database and router mount: `:155-170`
  - catch-all 404: `:172-176`.
- SRP — `OidcService` mixed concerns:
  `plugins/auth-backend/src/service/OidcService.ts:1-655`
  (redirect-URI validation at `:36-46` and `:55+`, CIMD usage via the
  import at `:34`, JWT decode via `decodeJwt` import at `:28`, DB access via
  `OidcDatabase` at `:30`, offline-access integration via `:33`).
- Mixed-concerns provider router with unrelated CORS helper:
  `plugins/auth-backend/src/providers/router.ts:34-136` (`bindProviderRouters`)
  and `:138-159` (`createOriginFilter` — does not belong here).
- Large but single-surface OIDC router:
  `plugins/auth-backend/src/service/OidcRouter.ts:1-582`.
- Clean satellites:
  `plugins/auth-backend/src/database/{AuthDatabase,OfflineSessionDatabase,OidcDatabase,UserInfoDatabase}.ts`,
  `plugins/auth-backend/src/identity/{TokenFactory,StaticTokenIssuer,KeyStores,DatabaseKeyStore,FirestoreKeyStore,MemoryKeyStore,StaticKeyStore}.ts`,
  `plugins/auth-backend/src/service/{CimdClient,OfflineAccessService,readTokenExpiration}.ts`,
  `plugins/auth-backend/src/actions/createWhoAmIAction.ts`.
- Module example (clean):
  `plugins/auth-backend-module-github-provider/src/{authenticator,resolvers,module}.ts`.

**Verdict — high severity SRP violations at the two routing composition
roots; otherwise clean.**

---

## 9. `packages/config` + `packages/config-loader`

The runtime configuration API and its loading layer.

| Principle | `packages/config` | `packages/config-loader` |
|-----------|-------------------|--------------------------|
| SRP | Borderline — `ConfigReader` (`reader.ts`, 484 LOC) implements eighteen methods of the `Config` interface plus `merge`, `cloneDeep`, and `typeOf` helpers. Single class, cohesive purpose, but large. | Respected — each source is its own class (`FileConfigSource`, `EnvConfigSource`, `RemoteConfigSource`, `StaticConfigSource`, `MutableConfigSource`, `MergedConfigSource`). |
| OCP | Respected. | Respected — adding a new config source means adding a new class implementing `ConfigSource`. |
| LSP | Respected. | Respected — all sources stream `AsyncConfigSourceGenerator` uniformly. |
| ISP | **Smell** — the `Config` interface declares eighteen methods: `has`, `keys`, `subscribe`, `get`, `getOptional`, `getConfig`, `getOptionalConfig`, `getConfigArray`, `getOptionalConfigArray`, `getNumber`, `getOptionalNumber`, `getBoolean`, `getOptionalBoolean`, `getString`, `getOptionalString`, `getStringArray`, `getOptionalStringArray`. Consumers that read a single string still depend on the full surface. Cohesive but fat; a per-type reader interface would honour ISP more strictly. | Respected. |
| DIP | Respected — application code depends on the `Config` interface, not on `ConfigReader`. | Respected. |

**Code references**

- ISP — fat `Config` interface (18 methods):
  `packages/config/src/types.ts:52-150`.
- `ConfigReader` implementation (~484 LOC, single class, borderline SRP):
  `packages/config/src/reader.ts:1-484`.
- Per-source classes (clean OCP/LSP):
  - `packages/config-loader/src/sources/FileConfigSource.ts`
  - `packages/config-loader/src/sources/EnvConfigSource.ts`
  - `packages/config-loader/src/sources/RemoteConfigSource.ts`
  - `packages/config-loader/src/sources/StaticConfigSource.ts`
  - `packages/config-loader/src/sources/MutableConfigSource.ts`
  - `packages/config-loader/src/sources/MergedConfigSource.ts`
- Source interface and base types:
  `packages/config-loader/src/sources/types.ts`.

**Verdict — `config-loader` is textbook good. `Config` has a medium-severity
ISP smell.**

---

## 10. `packages/cli`

The `backstage-cli` build/test/package entry point.

| Principle | Status | Notes |
|-----------|--------|-------|
| SRP | **Violated** at `CliInitializer` (242 LOC). It performs feature unwrapping, a CommonJS double-default-export workaround (`unwrapFeature`), promise resolution of lazy module loaders, conflict precedence between individually-added and array-sourced modules, command-graph registration, commander program construction, queue-based tree walk over the graph, manual argv re-parsing (lines 159–178 slice positional arguments by hand), action invocation, exit handling, and an `unhandledRejection` trap. Five or more concerns. |
| SRP | Respected at `CommandGraph` (158 LOC, single concern: sparse trie of commands) and `CommandRegistry` (28 LOC). |
| OCP | Respected | New CLI modules are added through `discoverCliModules.ts`; commander integration sits behind opaque module types so commands plug in without core edits. |
| LSP | Respected. | |
| ISP | Respected — `CliModule` and `CliCommand` types are small. |
| DIP | Minor concern — `CliInitializer.run()` directly imports `commander` and constructs `Command`. Swapping argument parsers would require changing this class. |

**Code references**

- SRP — `CliInitializer` mixed concerns:
  `packages/cli/src/wiring/CliInitializer.ts:48-219`. Specific concerns:
  - feature ingestion + promise handling: `:52-72`
  - graph registration per module: `:74-83`
  - individual-vs-array conflict precedence: `:85-109`
  - commander program construction + tree walk: `:117-145`
  - manual argv re-parsing (positional-arg slicing): `:159-178`
  - action invocation + CJS double-default handling: `:187-197`
  - exit / unhandled-rejection handling: `:198-217`.
- CJS interop helper (candidate for extraction):
  `packages/cli/src/wiring/CliInitializer.ts:222-242` (`unwrapFeature`).
- Clean satellites:
  `packages/cli/src/wiring/CommandGraph.ts:27-131` (single-concern sparse trie),
  `packages/cli/src/wiring/CommandRegistry.ts` (28 LOC, single concern),
  `packages/cli/src/wiring/discoverCliModules.ts`,
  `packages/cli/src/wiring/factory.ts`.
- Direct dependency on `commander` (DIP concern):
  `packages/cli/src/wiring/CliInitializer.ts:25` (`import { Command } from 'commander'`)
  and `:119` (`const program = new Command();`).

**Verdict — `CliInitializer` violates SRP. The graph and registry are
clean.**

---

## Heat Map

| Package group | Worst principle | Severity |
|---------------|-----------------|----------|
| `packages/backend-plugin-api` | — | none (exemplar) |
| `packages/backend-defaults` | — | none |
| `packages/catalog-model` | ISP | minor |
| `packages/core-plugin-api` | OCP | minor (legacy) |
| `packages/frontend-plugin-api` | — | none (replaces legacy) |
| `plugins/catalog` + `catalog-react` | — | none |
| `plugins/scaffolder` | ISP | minor |
| `packages/config` | ISP | medium |
| `packages/config-loader` | — | none |
| `plugins/auth-backend` | SRP | **high** |
| `plugins/catalog-backend` | SRP + ISP | **high** |
| `packages/cli` | SRP | **high** |

---

## Recommended Refactors (priority order)

### 1. Decompose `DefaultCatalogProcessingEngine` and `DefaultCatalogProcessingOrchestrator`

Extract:

- `ProcessingPollingLoop` — task pump, watermarks, scheduling.
- `OrphanCleaner` — orphan eviction on its own scheduler tick.
- `ProcessingResultHasher` — stable-stringify hash of `{completedEntity,
  deferredEntities, relations, refreshKeys, parents, errors}`.
- `ProcessingEventEmitter` — `events.publish` on the catalog-errors topic.
- `ProcessingTelemetry` — OpenTelemetry spans and metrics.

The engine becomes a thin composition root that wires these collaborators.

### 2. Split the `CatalogProcessor` interface

Replace the single optional-method interface with role-specific interfaces:

- `LocationReader { readLocation(...) }`
- `EntityPreProcessor { preProcessEntity(...) }`
- `EntityValidator { validateEntityKind(...) }`
- `EntityPostProcessor { postProcessEntity(...) }`

Concrete processors implement only the role(s) they fulfil. The orchestrator
dispatches by role, eliminating the optional-method fan-in.

### 3. Decompose `service/router.ts` in `plugins/auth-backend`

Extract:

- `createTokenIssuer(config, keyStore, ...)` — replaces the inline
  `StaticKeyStore` vs `TokenFactory` branch.
- `createSessionMiddleware(config, database)` — replaces lines 119–140
  (cookie parser, express-session, passport, KnexSessionStore).
- `assembleAuthRouter(...)` — the remaining wiring.

### 4. Split `service/OidcService.ts` in `plugins/auth-backend`

Suggested decomposition:

- `RedirectUriValidator` — RFC 8252 loopback handling and pattern matching.
- `OidcClientStore` — `OidcDatabase`-backed client/session reads and writes.
- `OidcTokenService` — issuance via `TokenIssuer` and offline-access
  integration.
- `CimdMetadataResolver` — CIMD URL validation and metadata fetch.

### 5. Decompose `CliInitializer`

Extract:

- `FeatureUnwrapper` — `unwrapFeature` and CJS interop, owned by its own
  module.
- `ModuleConflictResolver` — the individual-vs-array-source precedence rules.
- `CommanderProgramBuilder` — converts a `CommandGraph` to a populated
  `Command`. This also creates the seam needed to lift the direct dependency
  on `commander` (DIP improvement).

### 6. Narrow the `Config` interface (lower priority)

Consider introducing role-specific reader interfaces (for example
`StringConfig`, `OptionalStringConfig`, `ConfigSubtree`) that the existing
`Config` extends. Consumers can then accept the narrowest type they need.
This is a non-breaking change if introduced as a set of interfaces that
`Config` extends.

### 7. Move `createOriginFilter` out of `providers/router.ts`

Place it in a small `lib/origin.ts` (or similar) module. The current location
forces two unrelated concerns to share a file.

---

## Overall Assessment

Backstage's *new* core (`backend-plugin-api`, `backend-defaults`,
`frontend-plugin-api`, `config-loader/sources`) is an unusually clean
application of SOLID principles. The violations cluster in three places:

1. **Long-lived ingestion pipelines** — the catalog backend processing engine
   and orchestrator have accreted concerns over years and have become god
   classes.
2. **Composition roots** — `auth-backend`'s `service/router.ts`,
   `OidcService.ts`, and `cli`'s `CliInitializer` perform their own
   sub-system wiring inline rather than delegating to focused collaborators.
3. **Fat interfaces with optional members** — `CatalogProcessor` and, to a
   lesser extent, `Config` and `ActionContext` express multiple roles or
   concerns in a single type.

None of these violations threaten correctness; all are tractable through
focused, local refactors of the kind sketched above. The first two items in
the priority list would have the largest positive impact on
maintainability.

---

## Appendix — Violation Reference Index

Single-jump table for reviewers.

| # | Principle | Location | Severity |
|---|-----------|----------|----------|
| 1 | SRP | `plugins/catalog-backend/src/processing/DefaultCatalogProcessingEngine.ts:61-510` | high |
| 2 | SRP | `plugins/catalog-backend/src/processing/DefaultCatalogProcessingOrchestrator.ts:1-464` | high |
| 3 | ISP | `plugins/catalog-node/src/api/processor.ts:25-111` (`CatalogProcessor` fat interface) | high |
| 4 | SRP | `plugins/auth-backend/src/service/router.ts:61-179` (`createRouter` composition god-function) | high |
| 5 | SRP | `plugins/auth-backend/src/service/OidcService.ts:1-655` (multi-concern service) | high |
| 6 | SRP | `plugins/auth-backend/src/providers/router.ts:138-159` (`createOriginFilter` colocated with provider routing) | low |
| 7 | SRP | `plugins/auth-backend/src/service/OidcRouter.ts:1-582` (large but single OIDC surface) | low |
| 8 | SRP | `packages/cli/src/wiring/CliInitializer.ts:48-219` (multi-concern initializer) | high |
| 9 | DIP | `packages/cli/src/wiring/CliInitializer.ts:25,119` (direct `commander` coupling) | low |
| 10 | ISP | `packages/config/src/types.ts:52-150` (18-method `Config` interface) | medium |
| 11 | SRP | `packages/config/src/reader.ts:1-484` (`ConfigReader` borderline size) | low |
| 12 | OCP | `packages/core-plugin-api/src/plugin/Plugin.tsx:57-59` (`provide` visitor coupling, legacy) | low |
| 13 | ISP | `packages/catalog-model/src/entity/Entity.ts` (`Entity` super-union) | low |
| 14 | ISP | `plugins/scaffolder-node/src/actions/types.ts:32-110` (`ActionContext` bag) | low |

To grep this file later: search for any `path:line` token above to land
directly on the violation.
