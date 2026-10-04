const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "../out");
const mime = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".webp": "image/webp",
  ".woff2": "font/woff2",
  ".txt": "text/plain; charset=utf-8",
};
http
  .createServer((req, res) => {
    try {
      const pathname = decodeURIComponent(
        new URL(req.url, "http://127.0.0.1").pathname,
      );
      let target = path.resolve(root, "." + pathname);
      if (target !== root && !target.startsWith(root + path.sep)) {
        res.writeHead(403);
        res.end();
        return;
      }
      if (fs.existsSync(target) && fs.statSync(target).isDirectory())
        target = path.join(target, "index.html");
      if (!fs.existsSync(target)) {
        res.writeHead(404);
        res.end("Not found");
        return;
      }
      res.writeHead(200, {
        "Content-Type":
          mime[path.extname(target)] || "application/octet-stream",
        "X-Robots-Tag": "noindex, nofollow",
      });
      fs.createReadStream(target).pipe(res);
    } catch {
      res.writeHead(400);
      res.end("Bad request");
    }
  })
  .listen(3001, "127.0.0.1", () =>
    console.log("Static draft: http://127.0.0.1:3001/home-v2/"),
  );
