Runtime Dependencies Analysis Notes
📦 What This Analysis Is About
The point of this analysis was to figure out which packages Backstage actually needs at runtime — meaning in a real production environment, not just while building or testing. With a monorepo as large as Backstage, this isn't immediately obvious, so it made sense to approach it systematically.
🔍 Runtime vs. Dev Dependencies
In a package.json, dependencies split into two camps: "dependencies" are needed when the app is actually running, while "devDependencies" only matter during development or testing. This analysis focuses entirely on the former — if a package only shows up at build time, it's out of scope here.
🛠️ How I Approached It
I wrote a script called extract-runtime.js to automate the extraction process, since going through 228 packages by hand wasn't realistic. The script clones the Backstage repository, walks through every package folder, and pulls the "dependencies" field from each package.json it finds. It skips node_modules directories — otherwise the results would be polluted with transitive noise.
The output is a file called runtime-deps.json, which maps every package to its runtime dependencies.
bashnode extract-runtime.js
One thing worth noting: the script only captures direct runtime dependencies — what each package explicitly declares. Transitive dependencies (dependencies of dependencies) aren't in scope here, though they'd be the natural next step if this analysis were extended.
📊 Numbers

228 packages scanned in total
Results saved to runtime-deps.json

🧠 What I Found
Frontend packages are heavily React-based — react, react-dom, and react-router-dom appear constantly, alongside Material UI and Backstage's own core libraries like @backstage/core-plugin-api. Not surprising given Backstage is a React app, but the consistency across packages is notable.
Backend packages follow a fairly standard Node.js stack: Express for HTTP, Knex for database interactions, Winston for logging, and Zod for input validation. Nothing unusual here, but it confirms the backend isn't doing anything exotic at the infrastructure level.
Cross-cutting dependencies were the more interesting finding. Libraries like lodash, luxon, and zod show up across both frontend and backend packages repeatedly — suggesting they're treated as foundational utilities rather than package-specific choices. zod in particular appearing on both sides makes sense given the push toward consistent schema validation.
✅ Summary
Backstage's modularity means each of its 228 packages manages its own dependencies independently — but underneath that, there's a clear and consistent core. React and Material UI dominate the frontend; Express and Knex anchor the backend; and a small set of shared utilities runs through almost everything. Understanding this layer is useful for anyone trying to reason about what a production Backstage deployment actually needs to function.
