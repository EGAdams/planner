# Hook and Agent System Integration

## Critical Hook Requirements
**CRITICAL**: Any changes to hooks (.gemini/hooks/) or agent configurations require a user restart.

## When to Request Restart
- Modifying .gemini/hooks/pre-task.sh
- Modifying .gemini/hooks/post-task.sh  
- Modifying .gemini/settings.json hook configuration
- Changes to agent validation logic
- Updates to enforcement rules
- Creating or modifying .gemini/agents/ files
- Updates to behavioral system enforcement

## Restart Procedure
1. Commit changes first
2. Ask user to restart Gemini Code
3. DO NOT continue testing until restart confirmed
4. Never assume hooks or agents work without restart

## Hook-Agent Integration Points
- Pre-task hooks validate directive compliance
- Post-task hooks collect research metrics
- Agent handoff hooks ensure contract validation
- Emergency hooks trigger violation protocols