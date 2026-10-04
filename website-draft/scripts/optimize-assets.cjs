const path = require("node:path");
const fs = require("node:fs");
const sharp = require(process.argv[2] || "sharp");
const root = path.resolve(__dirname, "../public/media");
for (const slug of [
  "protect-recover",
  "cloud",
  "optinoc",
  "infrastructure",
  "itsm",
  "managed-services",
]) {
  fs.mkdirSync(path.join(root, "solutions", slug), { recursive: true });
  fs.writeFileSync(path.join(root, "solutions", slug, ".gitkeep"), "");
}
sharp(path.join(root, "solutions/optinoc/dashboard.png"))
  .resize({ width: 1237, withoutEnlargement: true })
  .webp({ quality: 84 })
  .toFile(path.join(root, "solutions/optinoc/dashboard.webp"))
  .then(() => console.log("Dashboard optimized."));
