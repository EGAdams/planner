#!/bin/bash

echo "Checking services for PhpMyAdmin..."

# Function to check and start a service
check_and_start() {
    SERVICE=$1
    if service "$SERVICE" status > /dev/null 2>&1; then
        echo "✅ $SERVICE is running."
    else
        echo "⚠️ $SERVICE is not running. Attempting to start..."
        if command -v sudo >/dev/null 2>&1; then
            sudo service "$SERVICE" start
        else
            service "$SERVICE" start
        fi
        
        # Check again
        if service "$SERVICE" status > /dev/null 2>&1; then
             echo "✅ $SERVICE started successfully."
        else
             echo "❌ Failed to start $SERVICE. Please check permissions."
        fi
    fi
}

check_and_start mysql
check_and_start apache2

echo ""
echo "-----------------------------------------------------"
echo "PhpMyAdmin Link:"
echo "http://localhost/phpmyadmin"
echo "-----------------------------------------------------"
echo ""
echo "Press Enter to return to menu..."
read
