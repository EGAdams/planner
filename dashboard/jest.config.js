const { createDefaultPreset } = require("ts-jest");

const tsJestTransformCfg = createDefaultPreset().transform;

/** @type {import("jest").Config} **/
module.exports = {
  testEnvironment: "node",
  transform: {
    ...tsJestTransformCfg,
  },
  testMatch: [
    "**/backend/__tests__/**/*.test.ts",
  ],
  testPathIgnorePatterns: [
    "/node_modules/",
    "/tests/",  // Ignore Playwright tests
    "\\.d\\.ts$",  // Ignore TypeScript declaration files
    "/dist/"  // Ignore compiled JS files
  ],
};