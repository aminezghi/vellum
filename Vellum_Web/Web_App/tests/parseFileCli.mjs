// Parse a bibliography file with the web app's own importer and print the
// records as JSON. Used by tools/test_cross_app_exchange.py to check that
// files exported by Vellum Desktop import cleanly into Vellum Web.
//
//   node tests/parseFileCli.mjs <path-to-file>
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import createJiti from "jiti";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");
const jiti = createJiti(rootDir, { alias: { "@": path.resolve(rootDir, "src") } });

const target = process.argv[2];
if (!target) {
  console.error("usage: node tests/parseFileCli.mjs <file>");
  process.exit(2);
}

const { parseUniversalFile } = jiti("./src/lib/activeLearning.ts");
const content = fs.readFileSync(target, "utf8");
const records = parseUniversalFile(content, path.basename(target));
process.stdout.write(JSON.stringify(records));
