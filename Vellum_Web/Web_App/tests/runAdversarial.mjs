import path from "node:path";
import { fileURLToPath } from "node:url";
import createJiti from "jiti";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");

const jiti = createJiti(rootDir, {
  alias: {
    "@": path.resolve(rootDir, "src"),
  },
});

console.log("=================================================");
console.log("Vellum_Web Adversarial Stress Test Suite");
console.log("=================================================\n");

try {
  console.log("▶ Loading tests/adversarial.test.ts...");
  jiti("./tests/adversarial.test.ts");
  console.log("✓ adversarial.test.ts registered.\n");
} catch (err) {
  console.error("Adversarial test registration failed:", err);
  process.exit(1);
}
