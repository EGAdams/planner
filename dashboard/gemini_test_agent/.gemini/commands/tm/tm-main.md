# Gemini Task Master Command Reference

Comprehensive command structure for Gemini Task Master integration with Gemini Code.

## Command Organization

Commands are organized hierarchically to match Gemini Task Master's CLI structure while providing enhanced Gemini Code integration.

## Project Setup & Configuration

### `/project:gemini-tm/init`
- `init-project` - Initialize new project (handles PRD files intelligently)
- `init-project-quick` - Quick setup with auto-confirmation (-y flag)

### `/project:gemini-tm/models`
- `view-models` - View current AI model configuration
- `setup-models` - Interactive model configuration
- `set-main` - Set primary generation model
- `set-research` - Set research model
- `set-fallback` - Set fallback model

## Task Generation

### `/project:gemini-tm/parse-prd`
- `parse-prd` - Generate tasks from PRD document
- `parse-prd-with-research` - Enhanced parsing with research mode

### `/project:gemini-tm/generate`
- `generate-tasks` - Create individual task files from tasks.json

## Task Management

### `/project:gemini-tm/list`
- `list-tasks` - Smart listing with natural language filters
- `list-tasks-with-subtasks` - Include subtasks in hierarchical view
- `list-tasks-by-status` - Filter by specific status

### `/project:gemini-tm/set-status`
- `to-pending` - Reset task to pending
- `to-in-progress` - Start working on task
- `to-done` - Mark task complete
- `to-review` - Submit for review
- `to-deferred` - Defer task
- `to-cancelled` - Cancel task

### `/project:gemini-tm/sync-readme`
- `sync-readme` - Export tasks to README.md with formatting

### `/project:gemini-tm/update`
- `update-task` - Update tasks with natural language
- `update-tasks-from-id` - Update multiple tasks from a starting point
- `update-single-task` - Update specific task

### `/project:gemini-tm/add-task`
- `add-task` - Add new task with AI assistance

### `/project:gemini-tm/remove-task`
- `remove-task` - Remove task with confirmation

## Subtask Management

### `/project:gemini-tm/add-subtask`
- `add-subtask` - Add new subtask to parent
- `convert-task-to-subtask` - Convert existing task to subtask

### `/project:gemini-tm/remove-subtask`
- `remove-subtask` - Remove subtask (with optional conversion)

### `/project:gemini-tm/clear-subtasks`
- `clear-subtasks` - Clear subtasks from specific task
- `clear-all-subtasks` - Clear all subtasks globally

## Task Analysis & Breakdown

### `/project:gemini-tm/analyze-complexity`
- `analyze-complexity` - Analyze and generate expansion recommendations

### `/project:gemini-tm/complexity-report`
- `complexity-report` - Display complexity analysis report

### `/project:gemini-tm/expand`
- `expand-task` - Break down specific task
- `expand-all-tasks` - Expand all eligible tasks
- `with-research` - Enhanced expansion

## Task Navigation

### `/project:gemini-tm/next`
- `next-task` - Intelligent next task recommendation

### `/project:gemini-tm/show`
- `show-task` - Display detailed task information

### `/project:gemini-tm/status`
- `project-status` - Comprehensive project dashboard

## Dependency Management

### `/project:gemini-tm/add-dependency`
- `add-dependency` - Add task dependency

### `/project:gemini-tm/remove-dependency`
- `remove-dependency` - Remove task dependency

### `/project:gemini-tm/validate-dependencies`
- `validate-dependencies` - Check for dependency issues

### `/project:gemini-tm/fix-dependencies`
- `fix-dependencies` - Automatically fix dependency problems

## Workflows & Automation

### `/project:gemini-tm/workflows`
- `smart-workflow` - Context-aware intelligent workflow execution
- `command-pipeline` - Chain multiple commands together
- `auto-implement-tasks` - Advanced auto-implementation with code generation

## Utilities

### `/project:gemini-tm/utils`
- `analyze-project` - Deep project analysis and insights

### `/project:gemini-tm/setup`
- `install-taskmaster` - Comprehensive installation guide
- `quick-install-taskmaster` - One-line global installation

## Usage Patterns

### Natural Language
Most commands accept natural language arguments:
```
/project:gemini-tm/add-task create user authentication system
/project:gemini-tm/update mark all API tasks as high priority
/project:gemini-tm/list show blocked tasks
```

### ID-Based Commands
Commands requiring IDs intelligently parse from $ARGUMENTS:
```
/project:gemini-tm/show 45
/project:gemini-tm/expand 23
/project:gemini-tm/set-status/to-done 67
```

### Smart Defaults
Commands provide intelligent defaults and suggestions based on context.