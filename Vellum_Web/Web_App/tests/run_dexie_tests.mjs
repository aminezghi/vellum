import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { exec } from "node:child_process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(__dirname, "..");

const server = http.createServer((req, res) => {
  const reqPath = req.url.split("?")[0];
  let filePath = path.join(appRoot, reqPath);
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath);
    const contentType = ext === ".js" ? "application/javascript" : ext === ".html" ? "text/html" : "text/plain";
    res.writeHead(200, { "Content-Type": contentType });
    fs.createReadStream(filePath).pipe(res);
  } else {
    res.writeHead(404);
    res.end("Not found: " + reqPath);
  }
});

server.listen(8999, () => {
  const chromePath = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
  const url = "http://localhost:8999/tests/dexie_adversarial_harness.html";
  const cmd = `"${chromePath}" --headless=new --disable-gpu --dump-dom "${url}"`;

  setTimeout(() => {
    exec(cmd, { maxBuffer: 10 * 1024 * 1024 }, (err, stdout, stderr) => {
      console.log("=================================================");
      console.log("Dexie Chrome Headless Execution Result:");
      console.log("=================================================\n");
      const match = stdout.match(/<pre id="output">([\s\S]*?)<\/pre>/);
      if (match) {
        console.log(match[1]);
      } else {
        console.log("Raw stdout snippet:\n", stdout.slice(0, 2000));
      }
      if (err) {
        console.error("Headless Chrome failed:", err.message, stderr ? `\n${stderr.slice(0, 2000)}` : "");
      }
      server.close();
      process.exit(err || !match ? 1 : 0);
    });
  }, 2500);
});
