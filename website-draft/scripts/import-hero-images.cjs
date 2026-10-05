const fs = require("node:fs");
const path = require("node:path");
const sharp = require("sharp");
const manifest = require("../content/image-prompts.json");
const sourceDirectory = process.argv[2];
if (!sourceDirectory)
  throw new Error("Provide the generated image source directory.");
Promise.all(
  manifest.assets.map(async (asset) => {
    const target = path.join(
      __dirname,
      "../public/media/solutions",
      asset.slug,
    );
    fs.mkdirSync(target, { recursive: true });
    const input = path.join(sourceDirectory, asset.originalFile);
    await sharp(input)
      .resize({ width: 1920, withoutEnlargement: true })
      .webp({ quality: 86 })
      .toFile(path.join(target, "hero-v3.webp"));
    await sharp(input)
      .resize({ width: 960, withoutEnlargement: true })
      .webp({ quality: 82 })
      .toFile(path.join(target, "hero-v3-mobile.webp"));
    console.log(asset.slug + ": saved desktop and mobile image");
  }),
).catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
