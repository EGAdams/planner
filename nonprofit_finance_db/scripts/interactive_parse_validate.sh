#!/bin/bash

# Interactive Parse and Validate Bank PDF Script
# Allows user to select a PDF file and runs validation

echo "=========================================="
echo "Parse and Validate Bank PDF"
echo "=========================================="

# Check MySQL connection FIRST - fail loudly if not available
echo ""
echo "Checking MySQL connection..."
# Test connection with the same credentials the Python script uses
# Load password from .env file
DB_PASSWORD=$(grep NON_PROFIT_PASSWORD /home/adamsl/planner/nonprofit_finance_db/.env | cut -d '=' -f2)
if ! mysql -h 127.0.0.1 -P 3306 -u adamsl -p"${DB_PASSWORD}" nonprofit_finance -e "SELECT 1;" &>/dev/null; then
    echo ""
    echo "**********************************************"
    echo "**********************************************"
    echo "**                                          **"
    echo "**   ERROR: Cannot connect to MySQL!       **"
    echo "**                                          **"
    echo "**********************************************"
    echo "**********************************************"
    echo ""
    echo "MySQL is not running or cannot be accessed."
    echo "Connection details:"
    echo "  Host: 127.0.0.1"
    echo "  Port: 3306"
    echo "  User: adamsl"
    echo ""
    echo "To fix this issue, try one of the following:"
    echo ""
    echo "1. Start MySQL service:"
    echo "   sudo service mysql start"
    echo ""
    echo "2. Or if using systemd:"
    echo "   sudo systemctl start mysql"
    echo ""
    echo "3. Check MySQL status:"
    echo "   sudo service mysql status"
    echo ""
    echo "4. Check if MySQL is listening on port 3306:"
    echo "   sudo netstat -tlnp | grep 3306"
    echo ""
    echo "5. If MySQL is not installed:"
    echo "   sudo apt-get install mysql-server"
    echo ""
    echo "6. Verify user 'adamsl' has access:"
    echo "   sudo mysql -e \"SELECT user, host FROM mysql.user WHERE user='adamsl';\""
    echo ""
    echo "**********************************************"
    echo ""
    exit 1
fi
echo "✓ MySQL connection successful (user: adamsl, database: nonprofit_finance)"
echo ""

# Check if PDF files exist in common locations
COMMON_DIRS=(
    "/mnt/c/Users/NewUser/Downloads"
    # "/mnt/c/Users/NewUser/Documents"
    # "/tmp"
    # "$(pwd)"
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
