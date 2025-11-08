# Agent Workspace

This directory is a temporary "scratchpad" for agents to use during their tasks.

## Overview

Inspired by the "scratchpad" concept for AI agents, this directory provides a sandboxed space for agents to perform file-based operations.

- **State Management:** Agents can write intermediate results, data, and context to files here, helping them manage state without overloading the context window.
- **Code Execution:** Agents can write scripts here to process data, run complex logic, or interact with tools. The agent can then execute the script and process the results.
- **Transience:** Files in this workspace are considered temporary and may be cleared between tasks. For long-term persistence, agents should save important scripts to the `/skills` directory.

This workspace is a core component of enabling agents to process data and execute code locally before returning only the most relevant information to the model.
