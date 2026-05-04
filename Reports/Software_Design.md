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
It'is a facade-structural pattern and it is used to hide the complexity of the interactions between an interface and many types and functions.
On [`types.ts`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/app/types.ts#L306) is defined the `BackstageApp` interface  with methods getPlugins(), getSystemIcon(), createRoot(), getProvider(), getRouter() with which the client interacts. This interface is implemented on AppManager.tsx which is wiring private attributes and methods together without exposing them.
For instance the consumer calls `createRoot()` which among other things indirectly calls a private method named [`getApiHolder`](https://github.com/Group06-SwDA/Backstage_snapshot/blob/master/packages/core-app-api/src/app/AppManager.tsx#L427-L523), which is longer and more complex than createRoot().

![](./Software_Deisgn_img/AppManager_facade.svg)

//Abstract Factory?? 
 
 