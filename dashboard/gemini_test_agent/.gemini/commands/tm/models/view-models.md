View current AI model configuration.

## Model Configuration Display

Shows the currently configured AI providers and models for Gemini Task Master.

## Execution

```bash
task-master models
```

## Information Displayed

1. **Main Provider**
   - Model ID and name
   - API key status (configured/missing)
   - Usage: Primary task generation

2. **Research Provider**
   - Model ID and name  
   - API key status
   - Usage: Enhanced research mode

3. **Fallback Provider**
   - Model ID and name
   - API key status
   - Usage: Backup when main fails

## Visual Status

```
Gemini Task Master AI Model Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Main:     ✅ gemini-1.5-pro (configured)
Research: ✅ gemini-1.5-flash (configured)  
Fallback: ⚠️  Not configured (optional)

Available Models:
- gemini-1.5-pro
- gemini-1.5-flash
```

## Next Actions

Based on configuration:
- If missing API keys → Suggest setup
- If no research model → Explain benefits
- If all configured → Show usage tips