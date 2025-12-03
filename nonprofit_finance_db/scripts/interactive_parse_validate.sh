#!/bin/bash

# Interactive Parse and Validate Bank PDF Script
# Allows user to select a PDF file and runs validation

echo "=========================================="
echo "Parse and Validate Bank PDF"
echo "=========================================="

# Check if PDF files exist in common locations
COMMON_DIRS=(
    "$HOME/Downloads"
    "$HOME/Documents"
    "/tmp"
    "$(pwd)"
)

echo ""
echo "Looking for PDF files in common locations..."
echo ""

# Find all PDF files and create a menu
PDF_FILES=()
for dir in "${COMMON_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        while IFS= read -r file; do
            if [ -f "$file" ]; then
                PDF_FILES+=("$file")
            fi
        done < <(find "$dir" -maxdepth 2 -name "*.pdf" -type f 2>/dev/null | head -20)
    fi
done

# Remove duplicates
PDF_FILES=($(printf '%s\n' "${PDF_FILES[@]}" | sort -u))

if [ ${#PDF_FILES[@]} -eq 0 ]; then
    echo "No PDF files found. Please provide a path."
    echo ""
    read -p "Enter full path to PDF file: " pdf_path
else
    echo "Found ${#PDF_FILES[@]} PDF file(s):"
    echo ""
    for i in "${!PDF_FILES[@]}"; do
        echo "$((i+1)). ${PDF_FILES[$i]}"
    done
    echo ""
    read -p "Enter number (1-${#PDF_FILES[@]}) or full path: " selection

    # Check if selection is a number
    if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le ${#PDF_FILES[@]} ]; then
        pdf_path="${PDF_FILES[$((selection-1))]}"
    else
        pdf_path="$selection"
    fi
fi

echo ""
echo "Using PDF: $pdf_path"
echo ""

# Validate file exists
if [ ! -f "$pdf_path" ]; then
    echo "✗ Error: File not found: $pdf_path"
    exit 1
fi

# Run the Python validation script
cd /home/adamsl/planner
python3 nonprofit_finance_db/scripts/parse_and_validate_pdf.py "$pdf_path" 1
exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✓ Validation completed successfully"
else
    echo "✗ Validation failed or encountered errors"
fi

exit $exit_code
