const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const api = path.join(root, "out", "api");
fs.mkdirSync(api, { recursive: true });
fs.copyFileSync(
  path.join(root, "hosting", "public", "contact.php"),
  path.join(api, "contact.php"),
);
console.log(
  "PHP contact endpoint included in static export; private config and schema excluded.",
);
