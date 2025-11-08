#!/bin/bash
#
# analyze_command_structure.sh
#
# Analyzes the subdirectory structure of a given path and counts the
# number of Markdown (.md) files in each subdirectory
#

TARGET_DIR="/home/adamsl/planner/.gemini/commands"

echo "Analyzing command structure in: $TARGET_DIR"
echo "============================================"

# Loop through each item in the target directory
for dir in "$TARGET_DIR"/*; do
  # Check if it's a directory
  if [ -d "$dir" ]; then
    # Find and count the .md files in the subdirectory
    count=$(find "$dir" -type f -name "*.md" | wc -l)
    # Print the directory name and the count
    dir_name=$(basename "$dir")
    printf "% -25s : %d markdown file(s)\n" "$dir_name" "$count"
  fi
done

echo "============================================"
echo "Analysis complete."
