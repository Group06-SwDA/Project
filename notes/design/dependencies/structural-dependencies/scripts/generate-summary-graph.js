const fs = require("fs");
const path = require("path");

const filePath = path.join(__dirname, "../structural-deps.json");
const data = JSON.parse(fs.readFileSync(filePath, "utf8"));

/*  Domain grouping */
const groupMap = {
  app: "Frontend",
  frontend: "Frontend",
  home: "Frontend",
  search: "Frontend",
  notifications: "Frontend",
  "user-settings": "Frontend",

  backend: "Backend",
  api: "Backend",
  auth: "Backend",
  catalog: "Backend",
  org: "Backend",
  permission: "Backend",
  "events-backend": "Backend",

  cli: "Tooling",
  devtools: "Tooling",
  "create-app": "Tooling",
  scaffolder: "Tooling",

  kubernetes: "Infrastructure",
  techdocs: "Infrastructure",

  core: "Core",
};

/*  Normalize package names (remove -react, /alpha, etc.) */
function normalize(name) {
  return name.split("/")[0].split("-")[0];
}

function group(name) {
  const base = normalize(name);
  return groupMap[base] || "Other";
}

/* Build collapsed edges */
const edges = new Set();

for (const key in data) {
  let [from, to] = key.split("-->").map((s) => s.trim());

  const gFrom = group(from);
  const gTo = group(to);

  // avoid self-loops
  if (gFrom !== gTo) {
    edges.add(`${gFrom} --> ${gTo}`);
  }
}

/* Output Mermaid-style diagram */
const output = ["graph TD", ...Array.from(edges)].join("\n");

fs.writeFileSync(
  path.join(__dirname, "../summary/summary-diagram.mmd"),
  output,
);
