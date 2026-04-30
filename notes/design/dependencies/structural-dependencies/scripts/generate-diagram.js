const fs = require("fs");
const path = require("path");

const filePath = path.join(__dirname, "../structural-deps.json");

const data = JSON.parse(fs.readFileSync(filePath, "utf8"));

let edges = [];

for (const key in data) {
  const [from, to] = key.split("-->");
  edges.push(`${from.trim()} --> ${to.trim()}`);
}

const output = `
graph TD
${edges.join("\n")}
`;

fs.writeFileSync(path.join(__dirname, "../diagram.mmd"), output);
