# MSI Installation Script for Planner Electron App

This document explains how to build and use the MSI installer for the Planner application.

## ✅ Current Status

**WORKING**:
- ✅ Linux AppImage build (`npm run build-linux`) - **120+ MB installer ready**
- ✅ MSI configuration complete and validated
- ✅ Cross-platform build script created

**REQUIRES SETUP**:
- ⚠️ Windows MSI build (needs wine on Linux or Windows environment)

## Prerequisites

### For MSI Building on Windows:
1. **Node.js** and **npm** installed
2. **Windows environment**
3. **electron-builder** dependencies installed (automatically handled by npm install)

### For MSI Building on Linux/WSL:
1. **Node.js** and **npm** installed
2. **Wine** installed: `sudo apt install wine`
3. **electron-builder** dependencies installed

### Alternative - Linux AppImage (Currently Working):
1. **Node.js** and **npm** installed
2. **electron-builder** dependencies installed

## Building Installers

### ✅ Linux AppImage (Working Now)
```bash
npm run build-linux
```
**Output**: `dist/Planner - AI Project Management-1.0.0.AppImage` (126+ MB)

### 🪟 Windows MSI (Requires Wine on Linux)

#### Option 1: Using the Build Script (Recommended)
```bash
npm run build-installer
```
- Automatically detects platform
- Falls back to Linux build if wine unavailable
- Provides detailed error messages and suggestions

#### Option 2: Direct MSI Build
```bash
npm run build-msi
```
**Requires**: Wine on Linux, or native Windows environment

#### Option 3: Build All Windows Installers
```bash
npm run dist
```
Creates both MSI and NSIS installers (requires Wine/Windows)

## Output

The built installer files will be located in the `dist/` directory:
- `Planner - AI Project Management Setup X.X.X.msi` - MSI installer
- `Planner - AI Project Management Setup X.X.X.exe` - NSIS installer (if built)

## Configuration

The MSI installer is configured with the following features:

### MSI-Specific Settings
- **Custom installation directory**: Users can choose where to install
- **Desktop shortcut**: Automatically created
- **Start menu shortcut**: Added to "Productivity" category
- **Shortcut name**: "Planner AI"

### Application Settings
- **App ID**: com.planner.app
- **Product Name**: Planner - AI Project Management
- **Architecture**: x64 only
- **Icon**: assets/icon.ico (you should add this file)

## Adding an Icon

To properly brand your installer:

1. Create or obtain an `.ico` file for Windows
2. Place it at `assets/icon.ico`
3. Optionally, also place a PNG version at `assets/icon.png`

## Troubleshooting

### Common Issues

1. **Missing Icon Warning**: If you see icon warnings, add proper icon files to the assets directory
2. **Build Failures**: Ensure all dependencies are installed with `npm install`
3. **Windows-specific Errors**: Some build operations require Windows or Windows build tools

### Cross-Platform Building

If building on non-Windows systems:
- Install Windows build tools for your platform
- Use Docker with Windows build environment
- Use a Windows virtual machine

## Installation Process

Once built, the MSI installer provides:
1. Welcome screen
2. License agreement (if configured)
3. Installation directory selection
4. Installation progress
5. Desktop/Start Menu shortcut creation
6. Completion confirmation

## Customizing the Installer

Edit the `build` section in `package.json` to customize:
- Product name and description
- Installation options
- Shortcuts and menu categories
- File associations
- Registry entries

## Distribution

The generated MSI file can be:
- Distributed directly to users
- Uploaded to download servers
- Included in software repositories
- Signed with code signing certificates (recommended for production)

## Security Note

For production distribution, consider:
- Code signing the MSI with a valid certificate
- Including virus scanning in your build process
- Testing installation on clean Windows systems