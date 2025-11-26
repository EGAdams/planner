#!/bin/bash
# Restore claude-code-collective backup from 2025-11-24T16:08:32.905Z

echo "🔄 Restoring claude-code-collective backup..."

# Copy backed up files back to project
cp -r "C:\Users\NewUser\Desktop\blue_time\planner\.claude-backups\1764000461160/"* "C:\Users\NewUser\Desktop\blue_time\planner/"

echo "✅ Restored successfully!"
echo "💡 You may need to restart Claude Code to reload configurations."
echo ""
echo "Backup location: C:\Users\NewUser\Desktop\blue_time\planner\.claude-backups\1764000461160"
