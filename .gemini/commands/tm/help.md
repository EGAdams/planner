Show help for Gemini Task Master commands.

Arguments: $ARGUMENTS

Display help for Gemini Task Master commands. If arguments provided, show specific command help.

## Gemini Task Master Command Help

### Quick Navigation

Type `/project:gemini-tm/` and use tab completion to explore all commands.

### Command Categories

#### 🚀 Setup & Installation
- `/project:gemini-tm/setup/install` - Comprehensive installation guide
- `/project:gemini-tm/setup/quick-install` - One-line global install

#### 📋 Project Setup
- `/project:gemini-tm/init` - Initialize new project
- `/project:gemini-tm/init/quick` - Quick setup with auto-confirm
- `/project:gemini-tm/models` - View AI configuration
- `/project:gemini-tm/models/setup` - Configure AI providers

#### 🎯 Task Generation
- `/project:gemini-tm/parse-prd` - Generate tasks from PRD
- `/project:gemini-tm/parse-prd/with-research` - Enhanced parsing
- `/project:gemini-tm/generate` - Create task files

#### 📝 Task Management
- `/project:gemini-tm/list` - List tasks (natural language filters)
- `/project:gemini-tm/show <id>` - Display task details
- `/project:gemini-tm/add-task` - Create new task
- `/project:gemini-tm/update` - Update tasks naturally
- `/project:gemini-tm/next` - Get next task recommendation

#### 🔄 Status Management
- `/project:gemini-tm/set-status/to-pending <id>`
- `/project:gemini-tm/set-status/to-in-progress <id>`
- `/project:gemini-tm/set-status/to-done <id>`
- `/project:gemini-tm/set-status/to-review <id>`
- `/project:gemini-tm/set-status/to-deferred <id>`
- `/project:gemini-tm/set-status/to-cancelled <id>`

#### 🔍 Analysis & Breakdown
- `/project:gemini-tm/analyze-complexity` - Analyze task complexity
- `/project:gemini-tm/expand <id>` - Break down complex task
- `/project:gemini-tm/expand/all` - Expand all eligible tasks

#### 🔗 Dependencies
- `/project:gemini-tm/add-dependency` - Add task dependency
- `/project:gemini-tm/remove-dependency` - Remove dependency
- `/project:gemini-tm/validate-dependencies` - Check for issues

#### 🤖 Workflows
- `/project:gemini-tm/workflows/smart-flow` - Intelligent workflows
- `/project:gemini-tm/workflows/pipeline` - Command chaining
- `/project:gemini-tm/workflows/auto-implement` - Auto-implementation

#### 📊 Utilities
- `/project:gemini-tm/utils/analyze` - Project analysis
- `/project:gemini-tm/status` - Project dashboard
- `/project:gemini-tm/learn` - Interactive learning

### Natural Language Examples

```
/project:gemini-tm/list pending high priority
/project:gemini-tm/update mark all API tasks as done
/project:gemini-tm/add-task create login system with OAuth
/project:gemini-tm/show current
```

### Getting Started

1. Install: `/project:gemini-tm/setup/quick-install`
2. Initialize: `/project:gemini-tm/init/quick`
3. Learn: `/project:gemini-tm/learn start`
4. Work: `/project:gemini-tm/workflows/smart-flow`

For detailed command info: `/project:gemini-tm/help <command-name>`