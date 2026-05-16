# Software Design
## Dependencies

### Code Dependencies
Code dependencies were extracted using the following `madge` command 

```bash
madge --json \
  --extensions ts,tsx \
  --ts-config /Backstage/Backstage_snapshot/tsconfig.json \
  --exclude '\.test\.(ts|tsx)$|\.spec\.(ts|tsx)$|\.stories\.(ts|tsx)$|__mocks__|__fixtures__|__tests__|\.d\.ts$|^\.storybook/' \
  /Backstage/Backstage_snapshot/packages/ \
  /Backstage/Backstage_snapshot/plugins/ \
  > deps.json
``` 
It builds a dependency graph from `import` statements in `.ts` and `.tsx` files. Test files, mocks, fixtures, stories, and type declarations were excluded to focus on production code only.

The analysis covers two top-level directories of the Backstage monorepo: `packages/`, which contains core libraries and shared infrastructure and `plugins/`, which contains independently deployable feature modules.

Using a python script it was possible to visualize dependency distribution

![](./Software_Deisgn_img/distribution_donut.png)
![](./Software_Deisgn_img/histogram.png)

The large majority of files have zero or very few dependencies.

The file which has the most dependencies is `packages/create-app/src/lib/versions.ts`, it references every package in the monorepo to keep version numbers aligned across releases. Its high count is structural.
The `models/index.ts` files are generated automatically from OpenAPI schemas and re-export every model in one place. 
Other notable entries include `packages/ui/src/index.ts` and `packages/core-components/src/components/index.ts`, both are public entry points for component libraries, designed to aggregate exports for consumers. `plugins/catalog-backend/src/service/CatalogBuilder.ts` is an exception: it is a manually written orchestrator that wires together many catalog services.

![](./Software_Deisgn_img/most15.png)


A large number of files have zero dependencies, such as components, icon definitions, theme tokens, and default configuration values. They are most common in `packages/app-defaults` and `packages/app-legacy` which are packages that provide stable defaults and are designed so that other files depend on them.

![](./Software_Deisgn_img/least15.png)

### Knowledge Dependencies

Knowledge dependencies measure how often two files are changed together in the same commit. Unlike code dependencies, they are derived from the history of the repository and reflect how the development team actually works in practice.

The git log was extracted from the Backstage snapshot (2026-04-09), then filtered using a bash script to remove bot commits, merge commits, and unusually large changesets, leaving 23630 commits for the analysis.

Coupling analysis was performed using `code-maat`

```bash
docker run -v /home/stealve/code_maat:/data code-maat \
  -l /data/git_log_filtered.log \
  -c git2 -a coupling \
  --min-revisions 5 --min-coupling 30 \
  > ../coupling.csv
```
In the obtained output the `degree` value (0–100%) represents the share of commits in which both files of a pair were modified together.
The `--min-revisions 5` parameter excludes file pairs where at least one file has been modified fewer than 5 times in total.
The `--min-coupling 30` parameter excludes pairs whose degree is below 30%.
The following graphs show how many co-change partners each file has.
 
![](./Software_Deisgn_img/knowledge_distribution_donut.png)
![](./Software_Deisgn_img/knowledge_histogram.png)

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

In `Backstage` the strategy is defined through the type [`TemplateAction`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/plugins/scaffolder-node/src/actions/types.ts#L113). One of the possible contexts that can be used is [`NunjucksWorkflowRunner`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/plugins/scaffolder-backend/src/scaffolder/tasks/NunjucksWorkflowRunner.ts#L329).
[`DefaultTemplateActionRegistry`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/plugins/scaffolder-backend/src/scaffolder/actions/TemplateActionRegistry.ts#L45)which is instantiated at startup by the client and implements the [`TemplateActionRegistry`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/plugins/scaffolder-backend/src/scaffolder/actions/TemplateActionRegistry.ts#L31) interface is not a strict GoF component needed to implement the strategy but serves a supporting role. It builds a dictionary of TemplateAction, one of which is returned to the context for example [`NunjucksWorkflowRunner`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/plugins/scaffolder-backend/src/scaffolder/tasks/NunjucksWorkflowRunner.ts#L329). There are some [builtin](https://github.com/Group06-SwDA/Backstage_snapshot/tree/5b61c2f33998f647b59f413bb2747983af15e8db/plugins/scaffolder-backend/src/scaffolder/actions/builtin) concrete strategies and some external [ones](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/plugins/scaffolder-backend-module-github/src/actions/github.ts#L51).
Each concrete action implements a different handler unknown to the client, executed by the [context](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/plugins/scaffolder-backend/src/scaffolder/tasks/NunjucksWorkflowRunner.ts#L530) by invoking its handler.
It is important to note that TemplateAction is a typescript Type and not an interface like in the GoF pattern but it plays the same role.
![](./Software_Deisgn_img/TemplateAction_Strategy.svg)

**Alternative: Template Method**
 An alternative to the Strategy could be the Template method, where a base abstract class would define a fixed execution structure leaving subclasses to implement only the specific behaviour but this would be less appropriate in this context since the concrete actions are too different from each other, having nothing in common except receiving an ActionContext.

### Builder
The third analysed pattern is a fluent-builder, a creational pattern, used to build a complex object piece by piece using several methods including the last one to finalize its creation. Forcing all DevApp configuration into a single constructor call would be unreadable and hard to extend.

In `Backstage` [`DevAppBuilder`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/dev-utils/src/devApp/render.tsx#L97) in `render.tsx` exposes methods like `registerPlugin()`, `addPage()`, and `addThemes()` that populate private arrays and return `this` for chaining. The React component tree is assembled only when [`build()`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/dev-utils/src/devApp/render.tsx#L229) is called inside [`render()`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/dev-utils/src/devApp/render.tsx#L309) which is the last method that the client calls to insert the DevApp in the DOM. [`createDevApp()`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/dev-utils/src/devApp/render.tsx#L340) instantiatiates a new builder. For `Backstage`, differently from pure GoF, there is only a concrete builder without an interface and each client is also a director since it chains every method it needs. One example of client is the [`catalog graph plugin`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/plugins/catalog-graph/dev/index.tsx#L167-234).

![](./Software_Deisgn_img/DevAppBuilder_builder.svg)

**Alternative: Abstract Factory**

A possible alternative is the following Abstract Factory. The concrete products rapresent the actual specific DOM components created by the builders. 
![](./Software_Deisgn_img/DevAppBuilder_abstract_factory.svg)
The pro is that it is not necessary to build the pipeline every time a DevApp is needed. The drawback is that is not incremental and not flexible. Each DevApp requires its own factory.
 
### Observer 

The Observer pattern, a behavioral pattern, is used when some changes in an object, called subject, influence others called observers. The subject keeps a collection of observers and notifies them of its changes.
In `Backstage` the concrete subject is represented by [`BehaviorSubject`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/packages/core-app-api/src/lib/subjects.ts#L125) which implements the [`Observable<T> type`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/packages/types/src/observable.ts#L63) and `ZenObservable.SubscriptionObserver<T>` which comes from the external library `zen-observable`. Both of them play the role of the GoF subject interface. In particular, the former exposes the `subscribe()` method and indirectly the `unsubscribe()` method through the [`Subscription type`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/packages/types/src/observable.ts#L33) and the latter exposes the methods `next()`, `error()` and `complete()` which correspond to the `notify()` in GoF. Specifically in `Backstage` `ZenObservable.SubscriptionObserver<T>` also represents the observer interface, so from the observer side subscribers implement this methods to receive updates on the subject, and from the subject side they are implemented to notify a new theme value.`BehaviorSubject` keeps a set of [`ZenObservable.SubscriptionObserver<T>`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/packages/core-app-api/src/lib/subjects.ts#L156-158) a collection of subscribers. One example of concrete observer is a lambda function defined in [`AppThemeSelector`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/packages/core-app-api/src/apis/implementations/AppThemeApi/AppThemeSelector.ts#L42-48) which is passed to the overloaded `subscribe` method instead of the one accepting only an [`Observer type`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/5b61c2f33998f647b59f413bb2747983af15e8db/packages/types/src/observable.ts#L22). The `Observer type` is not actually used in this example but could be used by other observer implementation. To summarize the user changes a theme and the subject notifies all observers about this change and each one implements its own logic, for example the one analysed persists the themeId in the browser. 

![](./Software_Deisgn_img/AppThemeSelector_observer.svg)

**Alternative: Command**

A possible alternative is a command, implemented as follows.
Here AppThemeSelector becomes an active component since it knows exactly which command to execute, while before it only sent notifications without knowing what concrete observers would have done.
![](./Software_Deisgn_img/AppThemeSelector_Command.svg)

The pro is that the relation between AppThemeSelector and the Receiver is explicit and easy to trace in the client and it is not necessary to send notifications. The drawback is that there is no dynamic subscription of observers so the invoker has to hold a list of command objects that are explicitly invoked so adding a new reaction requires modifying the invoker's command list.
