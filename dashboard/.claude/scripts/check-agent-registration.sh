#!/bin/bash
# Agent Registration Health Check
# Validates that all agent files are properly registered in agents.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
AGENTS_DIR="$PROJECT_ROOT/.claude/agents"
REGISTRY_FILE="$PROJECT_ROOT/.claude-collective/agents.md"

echo "========================================="
echo "Agent Registration Health Check"
echo "========================================="
echo ""
echo "Project Root: $PROJECT_ROOT"
echo "Agents Directory: $AGENTS_DIR"
echo "Registry File: $REGISTRY_FILE"
echo ""

# Check if directories exist
if [ ! -d "$AGENTS_DIR" ]; then
    echo "ERROR: Agents directory not found: $AGENTS_DIR"
    exit 1
fi

if [ ! -f "$REGISTRY_FILE" ]; then
    echo "ERROR: Registry file not found: $REGISTRY_FILE"
    exit 1
fi

echo "========================================="
echo "Agent Files Found:"
echo "========================================="

AGENT_FILES=()
UNREGISTERED_AGENTS=()
REGISTRATION_ISSUES=()

# Find all agent files
while IFS= read -r -d '' agent_file; do
    filename=$(basename "$agent_file")
    agent_name="${filename%.md}"

    echo ""
    echo "File: $filename"

    # Extract frontmatter name field
    frontmatter_name=$(awk '/^---$/{p++} p==1 && /^name:/{gsub(/^name: */, ""); print; exit}' "$agent_file")

    if [ -z "$frontmatter_name" ]; then
        echo "  WARNING: No 'name:' field found in frontmatter"
        REGISTRATION_ISSUES+=("$filename: Missing name in frontmatter")
    elif [ "$frontmatter_name" != "$agent_name" ]; then
        echo "  WARNING: Frontmatter name mismatch"
        echo "    Filename: $agent_name"
        echo "    Frontmatter: $frontmatter_name"
        REGISTRATION_ISSUES+=("$filename: Name mismatch (file: $agent_name, frontmatter: $frontmatter_name)")
    else
        echo "  Name: $frontmatter_name"
    fi

    # Check if registered in agents.md
    if grep -q "@$agent_name" "$REGISTRY_FILE"; then
        echo "  Status: REGISTERED in agents.md"
    else
        echo "  Status: NOT REGISTERED in agents.md"
        UNREGISTERED_AGENTS+=("$agent_name")
    fi

    # Check file permissions
    if [ ! -r "$agent_file" ]; then
        echo "  WARNING: File not readable"
        REGISTRATION_ISSUES+=("$filename: Not readable")
    fi

    AGENT_FILES+=("$agent_name")
done < <(find "$AGENTS_DIR" -maxdepth 1 -name "*.md" -type f -print0 | sort -z)

echo ""
echo "========================================="
echo "Summary:"
echo "========================================="
echo "Total agent files: ${#AGENT_FILES[@]}"
echo "Unregistered agents: ${#UNREGISTERED_AGENTS[@]}"
echo "Registration issues: ${#REGISTRATION_ISSUES[@]}"
echo ""

if [ ${#UNREGISTERED_AGENTS[@]} -gt 0 ]; then
    echo "UNREGISTERED AGENTS:"
    for agent in "${UNREGISTERED_AGENTS[@]}"; do
        echo "  - @$agent"
    done
    echo ""
fi

if [ ${#REGISTRATION_ISSUES[@]} -gt 0 ]; then
    echo "REGISTRATION ISSUES:"
    for issue in "${REGISTRATION_ISSUES[@]}"; do
        echo "  - $issue"
    done
    echo ""
fi

echo "========================================="
echo "Registry Content Check:"
echo "========================================="
echo "Agents listed in $REGISTRY_FILE:"
grep -o '@[a-z0-9-]*' "$REGISTRY_FILE" | sort -u | while read -r agent_ref; do
    agent_name="${agent_ref#@}"
    agent_file="$AGENTS_DIR/$agent_name.md"
    if [ -f "$agent_file" ]; then
        echo "  $agent_ref - FILE EXISTS"
    else
        echo "  $agent_ref - WARNING: FILE NOT FOUND"
    fi
done

echo ""
if [ ${#UNREGISTERED_AGENTS[@]} -eq 0 ] && [ ${#REGISTRATION_ISSUES[@]} -eq 0 ]; then
    echo "========================================="
    echo "RESULT: ALL AGENTS PROPERLY REGISTERED"
    echo "========================================="
    exit 0
else
    echo "========================================="
    echo "RESULT: REGISTRATION PROBLEMS FOUND"
    echo "========================================="
    exit 1
fi
