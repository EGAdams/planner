#!/bin/bash

# Install Wine and Build MSI Script for Planner Electron App
# This script installs wine and builds the MSI installer

echo "🍷 Installing Wine for Windows MSI building..."
echo "⚠️  Note: This requires sudo privileges"

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install wine
echo "🍷 Installing Wine..."
sudo apt install -y wine

# Verify wine installation
if command -v wine &> /dev/null; then
    echo "✅ Wine installed successfully!"
    wine --version
else
    echo "❌ Wine installation failed"
    exit 1
fi

echo ""
echo "🏗️  Now attempting to build MSI installer..."

# Try building MSI
npm run build-msi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ MSI installer built successfully!"
    echo "📦 Check the dist/ directory for your installer files"
    ls -la dist/*.msi dist/*.exe 2>/dev/null || echo "   (Files may have different extensions)"
else
    echo ""
    echo "⚠️  MSI build failed. This is common on WSL environments."
    echo "💡 Alternative options:"
    echo "   1. Use the Linux AppImage build: npm run build-linux"
    echo "   2. Build on a native Windows environment"
    echo "   3. Use Docker with Windows build environment"
fi