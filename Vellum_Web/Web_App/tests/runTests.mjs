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
console.log("Vellum_Web Automated Verification Test Suite");
console.log("=================================================\n");

// Load and execute test suites
try {
  console.log("▶ Loading tests/activeLearning.test.ts...");
  jiti("./tests/activeLearning.test.ts");
  console.log("✓ activeLearning.test.ts registered.\n");

  console.log("▶ Loading tests/universalParser.test.ts...");
  jiti("./tests/universalParser.test.ts");
  console.log("✓ universalParser.test.ts registered.\n");

  console.log("▶ Loading tests/apiRoutes.test.ts...");
  jiti("./tests/apiRoutes.test.ts");
  console.log("✓ apiRoutes.test.ts registered.\n");

  console.log("▶ Loading tests/batchDownloaderParser.test.ts...");
  jiti("./tests/batchDownloaderParser.test.ts");
  console.log("✓ batchDownloaderParser.test.ts registered.\n");

  console.log("▶ Loading tests/adversarial.test.ts...");
  jiti("./tests/adversarial.test.ts");
  console.log("✓ adversarial.test.ts registered.\n");
} catch (err) {
  console.error("Test execution failed:", err);
  process.exit(1);
}
