# Software Design

## Dependencies

### Code Dependencies

### Knowledge Dependencies

To analyse the knowledge dependencies the following pipeline was used
![](./Software_Deisgn_img/workflow_knoledge_d.png)
The end result is:
![](./Software_Deisgn_img/knowledge_dependencies.svg)

## Design Patterns

### Facade

The first analized code is [`AppManager.tsx`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/app/AppManager.tsx#L161).
It is a facade structural pattern and it is used to hide the complexity of the interactions between an interface and many types and functions.
On [`types.ts`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/app/types.ts#L306) is defined the `BackstageApp` interface  with methods getPlugins(), getSystemIcon(), createRoot(), getProvider(), getRouter() with which the client interacts. This interface is implemented on AppManager.tsx which is wiring private attributes and methods together without exposing them.
For instance the consumer calls `createRoot()` which among other things indirectly calls a private method named [`getApiHolder`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/app/AppManager.tsx#L427-L523), which is longer and more complex than createRoot().

![img](./Software_Deisgn_img/AppManager_facade.svg)

### Strategy

The [`resolveTheme`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/app/AppThemeProvider.tsx#L23-L47) function in `AppThemeProvider.tsx` is a strategy behavioral pattern used to separate the theme selection algorithm from the component that applies it.
[`AppThemeProvider`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/app/AppThemeProvider.tsx#L69) acts as the context: it calls `resolveTheme` passing `themeId`, `shouldPreferDark`, and the installed `themes`, without containing any selection logic itself. The strategy encapsulates a four-level fallback: match by explicit ID, prefer dark variant, fall back to light variant, fall back to the first available theme.

![](./Software_Deisgn_img/AppThemeProvider_strategy.svg)

### Builder

[`DevAppBuilder`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/dev-utils/src/devApp/render.tsx#L94) in `render.tsx` is a builder creational pattern that separates the step-by-step configuration of a dev application from its final assembly.
Methods like `registerPlugin()`, `addPage()`, and `addThemes()` each populate private arrays and return `this`, enabling method chaining without producing any output. The actual React component tree is assembled only when [`build()`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/dev-utils/src/devApp/render.tsx#L215) is called; the factory function [`createDevApp()`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/dev-utils/src/devApp/render.tsx#L325) acts as the director by instantiating a fresh builder.

![](./Software_Deisgn_img/DevAppBuilder_builder.svg)

### Observer

The observer behavioral pattern is split across [`subjects.ts`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/lib/subjects.ts) and [`AppThemeSelector.ts`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/apis/implementations/AppThemeApi/AppThemeSelector.ts): the former provides the reactive primitives, the latter uses them as a concrete subject.
`subjects.ts` defines [`BehaviorSubject<T>`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/lib/subjects.ts#L123), which holds a `Set` of active subscribers and fans out each `next(value)` call to all of them; unlike [`PublishSubject`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/lib/subjects.ts#L31), it also replays the current value to any new subscriber. `AppThemeSelector` holds a private `BehaviorSubject` and exposes it read-only via [`activeThemeId$()`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/apis/implementations/AppThemeApi/AppThemeSelector.ts#L78); when [`setActiveThemeId()`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/apis/implementations/AppThemeApi/AppThemeSelector.ts#L85) is called it notifies all observers in one step.

![](./Software_Deisgn_img/AppThemeSelector_observer.svg)
