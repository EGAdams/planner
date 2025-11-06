Check if Gemini Task Master is installed and install it if needed.

This command helps you get Gemini Task Master set up globally on your system.

## Detection and Installation Process

1. **Check Current Installation**
   ```bash
   # Check if gemini-task-master command exists
   which gemini-task-master || echo "Gemini Task Master not found"
   
   # Check npm global packages
   npm list -g gemini-task-master-ai
   ```

2. **System Requirements Check**
   ```bash
   # Verify Node.js is installed
   node --version
   
   # Verify npm is installed  
   npm --version
   
   # Check Node version (need 16+)
   ```

3. **Install Gemini Task Master Globally**
   If not installed, run:
   ```bash
   npm install -g gemini-task-master-ai
   ```

4. **Verify Installation**
   ```bash
   # Check version
   gemini-task-master --version
   
   # Verify command is available
   which gemini-task-master
   ```

5. **Initial Setup**
   ```bash
   # Initialize in current directory
   gemini-task-master init
   ```

6. **Configure AI Provider**
   Ensure you have at least one AI provider API key set:
   ```bash
   # Check current configuration
   gemini-task-master models --status
   
   # If no API keys found, guide setup
   echo "You'll need at least one API key:"
   echo "- GEMINI_API_KEY for Gemini"
   echo "- OPENAI_API_KEY for GPT models"
   echo "- GEMINI_API_KEY for research"
   echo ""
   echo "Set them in your shell profile or .env file"
   ```

7. **Quick Test**
   ```bash
   # Create a test PRD
   echo "Build a simple hello world API" > test-prd.txt
   
   # Try parsing it
   gemini-task-master parse-prd test-prd.txt -n 3
   ```

## Troubleshooting

If installation fails:

**Permission Errors:**
```bash
# Try with sudo (macOS/Linux)
sudo npm install -g gemini-task-master-ai

# Or fix npm permissions
npm config set prefix ~/.npm-global
export PATH=~/.npm-global/bin:$PATH
```

**Network Issues:**
```bash
# Use different registry
npm install -g gemini-task-master-ai --registry https://registry.npmjs.org/
```

**Node Version Issues:**
```bash
# Install Node 18+ via nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

## Success Confirmation

Once installed, you should see:
```
✅ Gemini Task Master v0.16.2 (or higher) installed
✅ Command 'gemini-task-master' available globally
✅ AI provider configured
✅ Ready to use slash commands!

Try: /project:gemini-task-master:init your-prd.md
```

## Next Steps

After installation:
1. Run `/project:gemini-utils:check-health` to verify setup
2. Configure AI providers with `/project:gemini-task-master:models`
3. Start using Gemini Task Master commands!