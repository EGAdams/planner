#!/usr/bin/env node
// tools/codex_tester_bridge.mjs
//
// Bridge between Python and the Codex SDK for test generation.
// - Reads JSON from stdin
// - Runs Codex in workspace-write mode
// - Lets Codex create/update test files
// - Emits a small JSON report to stdout

import { Codex } from "@openai/codex-sdk";
import fs from "node:fs";
import path from "node:path";

async function readStdin() {
  return new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", chunk => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    process.stdin.on("error", reject);
  });
}

async function main() {
  try {
    const raw = await readStdin();
    let payload;
    try {
      payload = JSON.parse(raw || "{}");
    } catch (err) {
      throw new Error("Invalid JSON payload on stdin");
    }

    const {
      spec = "",
      implementation = "",
      language = "python",
      testFramework = "pytest",
      fileName = "test_generated_code.py",
      workspaceDir = process.cwd(),
      model,
    } = payload;

    if (!spec.trim()) {
      throw new Error("Missing 'spec' in payload");
    }

    // Ensure workspace exists
    fs.mkdirSync(workspaceDir, { recursive: true });

    const codex = new Codex();

    const thread = codex.startThread({
      model,
      sandboxMode: "workspace-write",
      workingDirectory: workspaceDir,
      skipGitRepoCheck: true,
    });

    const instructions = `
You are an elite software test engineer (Codex Tester Agent).

Goal:
- Using the feature specification and (optional) implementation, generate a comprehensive test suite.
- Use the test framework: ${testFramework}.
- Use the language: ${language}.
- Work directly inside the workspace directory: "${workspaceDir}".
- Create or overwrite the main test file: "${fileName}".
- You may create additional helper or fixture files if helpful.
- Do NOT print the full test file contents in your final response; only summarize what you did.

<spec>
${spec}
</spec>

<implementation>
${implementation}
</implementation>

When you are done:
- Ensure tests are syntactically valid and consistent with the implementation/spec.
- Leave the workspace in a consistent state.
`;

    const turn = await thread.run(instructions);

    const createdFiles = [];
    const updatedFiles = [];
    const deletedFiles = [];

    for (const item of turn.items || []) {
      if (item.type === "file_change") {
        for (const change of item.changes || []) {
          const fullPath = path.resolve(workspaceDir, change.path);
          if (change.kind === "add") {
            createdFiles.push(fullPath);
          } else if (change.kind === "update") {
            updatedFiles.push(fullPath);
          } else if (change.kind === "delete") {
            deletedFiles.push(fullPath);
          }
        }
      }
    }

    const primaryFile = path.resolve(workspaceDir, fileName);

    const report = {
      status: "success",
      model: model ?? null,
      threadId: thread.id,
      workingDirectory: workspaceDir,
      primaryFile,
      createdFiles,
      updatedFiles,
      deletedFiles,
      notes: turn.finalResponse,
      usage: turn.usage,
    };

    process.stdout.write(JSON.stringify(report));
  } catch (err) {
    const errorReport = {
      status: "error",
      message: err?.message ?? String(err),
      stack: err?.stack ?? null,
    };
    process.stdout.write(JSON.stringify(errorReport));
    process.exitCode = 1;
  }
}

main();
