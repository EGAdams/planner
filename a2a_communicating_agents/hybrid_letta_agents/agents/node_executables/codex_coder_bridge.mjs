#!/usr/bin/env node
// tools/codex_coder_bridge.mjs
//
// Bridge between Python and the Codex SDK.
// Reads a JSON payload from stdin, runs Codex in workspace-write mode,
// lets Codex create/edit files, then prints a small JSON report to stdout.

import { Codex } from "@openai/codex-sdk";
import fs from "node:fs";
import path from "node:path";

async function readStdin() {
  return new Promise<string>((resolve, reject) => {
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
    const payload = JSON.parse(raw || "{}");

    const spec: string = payload.spec ?? "";
    const language: string = payload.language ?? "python";
    const fileName: string = payload.fileName ?? "generated_code.py";
    const workspaceDir: string = payload.workspaceDir ?? process.cwd();
    const model: string | undefined = payload.model || undefined;

    if (!spec.trim()) {
      throw new Error("Missing 'spec' in payload");
    }

    // Ensure workspace exists
    fs.mkdirSync(workspaceDir, { recursive: true });

    // Instantiate Codex (will reuse CLI auth/config by default)
    const codex = new Codex();

    const thread = codex.startThread({
      model,
      sandboxMode: "workspace-write",
      workingDirectory: workspaceDir,
      skipGitRepoCheck: true,
    });

    const instructions = `
You are an elite software engineer (Codex Coder Agent).

Task:
- Implement the feature described in the <spec> below.
- Use the target language: ${language}.
- Work directly inside the current workspace directory ("${workspaceDir}").
- Create or overwrite the main implementation file: "${fileName}".
- Feel free to create additional helper files or tests as needed.
- Do NOT print full file contents in your final explanation; only summaries.

<spec>
${spec}
</spec>

When you are done:
- Ensure the code compiles (or is at least syntactically valid).
- Ensure the workspace is left in a consistent state.
`;

    const turn = await thread.run(instructions);

    // Inspect file changes using Codex SDK event items.
    const createdFiles: string[] = [];
    const updatedFiles: string[] = [];
    const deletedFiles: string[] = [];

    for (const item of turn.items) {
      if (item.type === "file_change") {
        for (const change of item.changes) {
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
      // Final natural-language summary from Codex:
      notes: turn.finalResponse,
      // Optional: usage info from Codex (tokens etc.)
      usage: turn.usage,
    };

    process.stdout.write(JSON.stringify(report));
  } catch (err: any) {
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
