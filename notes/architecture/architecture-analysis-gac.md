# Architecture
( **File done following the original docs, to check the actual code to see if they correspond** )
check this chat to undestand how to use fitness functions on typescript to assert architecture correctness https://gemini.google.com/share/d060632099ce
## Plugin Architecture

Three different Forms 

### Standalone

A standalone plugin in a Plugin Architecture, is a self-contained, independently deployable module that adds specifc capabilities or technical features to the core system. 

1. **High Cohesion:** The plugin encapsulates everything it needs to perform its specific task 
2. **Low Coupling:** It does not depend on other plugins to function. 

In the backstage app the standalone plugins are used to render hardcoded informations, like static data or dynamic data insert in forms. See the radar plugin, to find in the code.

### Service backend

### Third-party backend
