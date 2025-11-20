#!/usr/bin/env node

/**
 * Cross-Platform Build Script for Planner Electron App
 *
 * This script builds installers for the Planner application.
 * It automatically detects the platform and builds appropriate installers.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const platform = os.platform();
const isWindows = platform === 'win32';
const isLinux = platform === 'linux';
const isMac = platform === 'darwin';

console.log(`🏗️  Building Planner Installer for ${platform}...\n`);

// Check if assets directory exists
const assetsDir = path.join(__dirname, 'assets');
if (!fs.existsSync(assetsDir)) {
    console.log('📁 Creating assets directory...');
    fs.mkdirSync(assetsDir, { recursive: true });
}

// Check if icon exists
const iconPath = path.join(assetsDir, 'icon.ico');
const pngIconPath = path.join(assetsDir, 'icon.png');

if (!fs.existsSync(iconPath) && !fs.existsSync(pngIconPath)) {
    console.log('⚠️  Warning: No icon found at assets/icon.ico or assets/icon.png');
    console.log('   The build will continue but the app may not have an icon.');
    console.log('   Consider adding a proper icon file to the assets directory.\n');
}

// Check for wine on Linux when building Windows targets
function checkWineAvailability() {
    try {
        execSync('which wine', { stdio: 'ignore' });
        return true;
    } catch (error) {
        return false;
    }
}

function buildForPlatform() {
    try {
        console.log('🔨 Running electron-builder...');
        console.log('   This may take a few minutes depending on your system...\n');

        let buildCommand;

        if (isWindows) {
            // On Windows, build MSI directly
            buildCommand = 'npm run build-msi';
            console.log('🪟 Building Windows MSI installer...');
        } else if (isLinux) {
            // On Linux, check if we should build Windows or Linux targets
            const hasWine = checkWineAvailability();

            if (hasWine) {
                // Build Windows MSI with wine
                buildCommand = 'npm run build-msi';
                console.log('🍷 Building Windows MSI installer using Wine...');
            } else {
                // Build Linux packages instead
                buildCommand = 'npm run build-linux';
                console.log('🐧 Wine not available. Building Linux packages instead...');
                console.log('   To build Windows MSI on Linux, install wine: sudo apt install wine');
            }
        } else if (isMac) {
            // On macOS, build native or try Windows with wine
            buildCommand = 'npm run build-native';
            console.log('🍎 Building native macOS installer...');
        } else {
            // Fallback to native build
            buildCommand = 'npm run build-native';
            console.log(`⚙️  Building native installer for ${platform}...`);
        }

        execSync(buildCommand, {
            stdio: 'inherit',
            cwd: __dirname
        });

        console.log('\n✅ Installer built successfully!');
        console.log('📦 Output files located in: ./dist/');

        // List the generated files
        const distDir = path.join(__dirname, 'dist');
        if (fs.existsSync(distDir)) {
            const files = fs.readdirSync(distDir);
            console.log('\n📋 Generated files:');
            files.forEach(file => {
                const filePath = path.join(distDir, file);
                if (fs.statSync(filePath).isFile()) {
                    const stats = fs.statSync(filePath);
                    const sizeMB = (stats.size / (1024 * 1024)).toFixed(2);
                    console.log(`   • ${file} (${sizeMB} MB)`);
                }
            });
        }

        return true;

    } catch (error) {
        console.error('\n❌ Build failed:');
        console.error(error.message);

        // Provide helpful suggestions based on the error
        if (error.message.includes('wine is required')) {
            console.log('\n💡 Suggestions:');
            console.log('   1. Install wine: sudo apt install wine');
            console.log('   2. Or build Linux packages instead: npm run build-linux');
            console.log('   3. Or use a Windows machine/VM for MSI builds');
        }

        return false;
    }
}

// Main execution
const success = buildForPlatform();
process.exit(success ? 0 : 1);