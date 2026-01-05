# TODO

## Task Master Setup

- [ ] Create or obtain a PRD (Product Requirements Document)
  - Place it in `.taskmaster/docs/prd.txt` or `.taskmaster/docs/prd.md`
  - Can describe features, requirements, or improvements needed

- [ ] Parse the PRD to generate tasks
  ```bash
  task-master parse-prd .taskmaster/docs/prd.txt
  ```

- [ ] Analyze task complexity (optional but recommended)
  ```bash
  task-master analyze-complexity --research
  ```

- [ ] Expand tasks into subtasks
  ```bash
  task-master expand --all --research
  ```

- [ ] Start working on tasks
  ```bash
  task-master next
  task-master show <id>
  ```

## Notes

- Task Master is already initialized in this project
- Configuration is at `.taskmaster/config.json`
- Using Claude Code (Sonnet) for all AI operations
