import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
export default defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    files: ["scripts/*.cjs"],
    rules: { "@typescript-eslint/no-require-imports": "off" },
  },
  globalIgnores(["out/**", ".next/**", "next-env.d.ts", "qa-artifacts/**"]),
]);
