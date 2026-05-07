# Software Design
## Dependencies
### Code Dependencies
### Knowledge Dependencies

## Design Patterns

### Facade

The first analized pattern is a facade, a structural pattern, and it is used to hide the complexity of the interactions between an interface and many types and functions because exposing them  directly would force every consumer to understand and coordinate them. Without the facade, adding or refactoring an internal component would require changes in every caller. In `Backstage` the facade is seen in [`AppManager.tsx`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/app/AppManager.tsx#L161).
On [`types.ts`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/app/types.ts#L306) is defined the `BackstageApp` interface  with methods getPlugins(), getSystemIcon(), createRoot(), getProvider(), getRouter() with which the client interacts. This interface is implemented on AppManager.tsx which is wiring private attributes and methods together without exposing them to the caller.
The final consumer is [`App.tsx`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/app/src/App.tsx) which instantiates the app through [`createApp`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/app-defaults/src/createApp.tsx`#L36) which in turn calls `createSpecializedApp()`.

For instance the consumer calls `createRoot()` which among other things indirectly calls a private method named [`getApiHolder()`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/app/AppManager.tsx#L427-L523), which is longer and more complex than createRoot().

![img](./Software_Deisgn_img/AppManager_facade.svg)

**Alternative**: There is not an efficient and clear alternative to this pattern.
It is possible to evaluate a Singleton to guarantee one single instance of the App and a builder to simplify its [`creation`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/app/src/App.tsx#L132). An Abastract Factory can also be used but AppManager links together etherogeneous elements so it would not be the right choice. All alternatives address construction or instantiation concerns, but neither hides the internal complexity of the subsystem from the consumer, which is the core responsibility of the Facade.

### Strategy

The second analysed pattern is a Strategy, a behavioral pattern,used to define a family of interchangeable algorithms to be replaced or tested in isolation, without touching the client since the algorithm is decoupled from the object which is using it.

In `Backstage` the strategy is defined through the type [`TemplateAction`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/plugins/scaffolder-node/src/actions/types.ts#L113). The context is[`DefaultTemplateActionRegistry`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/plugins/scaffolder-backend/src/scaffolder/actions/TemplateActionRegistry.ts#L45)which is instantiated at startup and implements the [`TemplateActionRegistry`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/plugins/scaffolder-backend/src/scaffolder/actions/TemplateActionRegistry.ts#L31) interface. The latter builds a dictionary of TemplateAction which are returned to the runner for example [`NunjucksWorkflowRunner`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/plugins/scaffolder-backend/src/scaffolder/tasks/NunjucksWorkflowRunner.ts#L329). There are some [builtin](https://github.com/Group06-SwDA/Backstage_snapshot/tree/5b61c2f33998f647b59f413bb2747983af15e8db/plugins/scaffolder-backend/src/scaffolder/actions/builtin) concrete strategies and some external [ones](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/plugins/scaffolder-backend-module-github/src/actions/github.ts#L51).
Each concrete action implements a different handler unknown to the client which just calls [it](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/plugins/scaffolder-backend/src/scaffolder/tasks/NunjucksWorkflowRunner.ts#L530).
![](./Software_Deisgn_img/TemplateAction_Strategy.svg)

**Alternative: Template Method**
 An alternative to the Strategy could be the Template method, where a base abstract class would define a fixed execution structure leaving subclasses to implement only the specific behaviour but this would be less appropriate in this context since the concrete actions are too different from each other, having nothing in common except receiving an ActionContext.

### Builder
The third analysed pattern is a builder, a creational pattern, used to build piece by piece a complex object using method for building it at the end.

In `Backstage`[`DevAppBuilder`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/dev-utils/src/devApp/render.tsx#L94) in `render.tsx` exposes methods like `registerPlugin()`, `addPage()`, and `addThemes()` that populate private arrays and return `this` for chaining. The React component tree is assembled only when [`build()`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/dev-utils/src/devApp/render.tsx#L215) is called; [`createDevApp()`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/dev-utils/src/devApp/render.tsx#L325) acts as director by instantiating a fresh builder.

![](./Software_Deisgn_img/DevAppBuilder_builder.svg)

**Which classes play which role?**

- **Builder**: `DevAppBuilder`, accumulates configuration through chainable methods (`registerPlugin`, `addPage`, `addThemes`).
- **Director**: `createDevApp()`, instantiates a fresh builder and drives the construction sequence.

**Why is the pattern used?**
A dev app has many optional parts (plugins, pages, themes) that need to be composed incrementally. Forcing all configuration into a single constructor call would be unreadable and hard to extend.

**Which problem does it solve?**
It avoids a constructor with a large number of optional parameters and decouples the configuration phase from the construction phase: `build()` can enforce invariants once, rather than on every setter call.

**Alternative: Abstract Factory**
Abstract Factory also creates complex objects without exposing their concrete classes, but it produces families of related products in one shot rather than assembling a single object step by step.

- *Pro*: good when several related objects must always be created together; no director or chaining API needed.
- *Con*: all products are created at once, no incremental or conditional assembly; harder to enforce that certain steps happen before others; optional parts need extra factory variants.

### Observer

[`subjects.ts`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/lib/subjects.ts) defines [`BehaviorSubject<T>`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/lib/subjects.ts#L123), which holds a `Set` of active subscribers and fans out each `next(value)` to all of them, replaying the current value to any new subscriber (unlike [`PublishSubject`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/lib/subjects.ts#L31)). [`AppThemeSelector`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/apis/implementations/AppThemeApi/AppThemeSelector.ts) wraps a private `BehaviorSubject` exposed read-only via [`activeThemeId$()`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/apis/implementations/AppThemeApi/AppThemeSelector.ts#L78): calling [`setActiveThemeId()`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/apis/implementations/AppThemeApi/AppThemeSelector.ts#L85) notifies all observers: `useObservable` re-renders the UI and the observer in [`createWithStorage()`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/apis/implementations/AppThemeApi/AppThemeSelector.ts#L30) persists the choice to `localStorage`.

![](./Software_Deisgn_img/AppThemeSelector_observer.svg)

**Which classes play which role?**

- **Subject**: `AppThemeSelector`, holds the state and exposes `activeThemeId$()` for subscription.
- **Concrete observable**: `BehaviorSubject<T>` in `subjects.ts`, manages the subscriber set and fans out notifications; replays the current value to new subscribers.
- **Observers**: `useObservable` in `AppThemeProvider` (re-renders the UI) and the storage callback in `createWithStorage()`

**Why is the pattern used?**
Two independent reactions (UI update and persistence) must happen whenever the active theme changes. The observer pattern lets both subscribe without `AppThemeSelector` knowing about either of them.

**Which problem does it solve?**
It decouples the source of a state change from everything that must react to it. Without the pattern, `setActiveThemeId()` would have to call the UI updater and the storage writer explicitly, creating direct dependencies on both.

**Alternative: Command**
Instead of observers subscribing dynamically, the subject could hold a list of Command objects that are explicitly invoked when the state changes, each encapsulating one reaction.

- *Pro*: explicit and easy to trace; supports undo/redo and logging; no hidden notification chain.
- *Con*: tight coupling between the subject and the specific commands it must invoke; no dynamic subscribe/unsubscribe; adding a new reaction requires modifying the subject's command list.
