# Migration Package - Documentation Overview

This package contains everything needed to migrate the Agent Communication System to a new location.

---

## Documents Included

### 📘 1. AGENT_COMMUNICATION_SYSTEM_MIGRATION_GUIDE.md
**Purpose:** Complete, detailed migration guide
**Who should read:** Anyone doing the migration (read this first)
**Length:** ~600 lines
**Contains:**
- Detailed explanation of how the system works
- Complete file list with full paths
- Step-by-step migration instructions
- Configuration guide
- Testing procedures
- Troubleshooting section

**Use this if:** You want complete details and explanations

---

### 📄 2. MIGRATION_QUICK_REFERENCE.txt
**Purpose:** Quick reference with just file paths and commands
**Who should read:** Engineers who just need the file list
**Length:** Short text file
**Contains:**
- All 27 file paths (plain text list)
- Python dependencies
- Environment variables
- Quick start commands

**Use this if:** You just need to know which files to copy

---

### 📝 3. SIMPLE_MIGRATION_INSTRUCTIONS.md
**Purpose:** Simplified instructions for quick migration
**Who should read:** Engineers who want the simplest explanation
**Length:** ~200 lines
**Contains:**
- Simple 3-step process
- Manual and automated options
- Common problems & solutions
- Quick commands cheat sheet

**Use this if:** You want the quickest way to migrate

---

### 🔧 4. migrate_agent_system.sh
**Purpose:** Automated migration script
**Who should use:** Anyone who wants automation
**Type:** Bash script (executable)
**What it does:**
- Checks prerequisites
- Creates directory structure
- Copies all files
- Sets up Python virtual environment
- Installs dependencies
- Creates configuration files
- Runs verification tests

**Use this if:** You want the script to do everything automatically

**Usage:**
```bash
./migrate_agent_system.sh /path/to/destination
```

---

### 📋 5. MIGRATION_PACKAGE_README.md
**Purpose:** This file - explains what each document is
**Who should read:** Start here to understand what you have

---

## Which Document Should You Use?

### Scenario 1: "I just want it done fast"
→ Use: `migrate_agent_system.sh` (automated script)
→ Backup: `SIMPLE_MIGRATION_INSTRUCTIONS.md`

### Scenario 2: "I need to understand how it works"
→ Use: `AGENT_COMMUNICATION_SYSTEM_MIGRATION_GUIDE.md`

### Scenario 3: "I just need the file list"
→ Use: `MIGRATION_QUICK_REFERENCE.txt`

### Scenario 4: "I'm not very technical"
→ Use: `SIMPLE_MIGRATION_INSTRUCTIONS.md`
→ Then use: `migrate_agent_system.sh`

### Scenario 5: "Something went wrong"
→ Use: `AGENT_COMMUNICATION_SYSTEM_MIGRATION_GUIDE.md` (Troubleshooting section)

---

## Recommended Workflow

### For Most Engineers:

1. **Read:** `SIMPLE_MIGRATION_INSTRUCTIONS.md` (5 minutes)
2. **Run:** `./migrate_agent_system.sh /your/path` (10 minutes)
3. **Test:** Follow the prompts from the script
4. **Done!**

### If Script Fails:

1. **Check:** `AGENT_COMMUNICATION_SYSTEM_MIGRATION_GUIDE.md` → Troubleshooting
2. **Try:** Manual migration using Step-by-Step guide
3. **Verify:** Run test scripts manually

---

## Quick Start (TL;DR)

```bash
# 1. Read the simple instructions
cat SIMPLE_MIGRATION_INSTRUCTIONS.md

# 2. Run the automated script
./migrate_agent_system.sh /your/new/path

# 3. Follow the prompts

# Done!
```

---

## File Summary

| File | Size | Purpose | Read Time |
|------|------|---------|-----------|
| AGENT_COMMUNICATION_SYSTEM_MIGRATION_GUIDE.md | Large | Complete guide | 20 min |
| MIGRATION_QUICK_REFERENCE.txt | Small | File paths only | 2 min |
| SIMPLE_MIGRATION_INSTRUCTIONS.md | Medium | Simple guide | 5 min |
| migrate_agent_system.sh | Script | Automation | N/A (run it) |
| MIGRATION_PACKAGE_README.md | Small | This file | 3 min |

---

## What Gets Migrated

**Total Files:** 27 required files + documentation
**Total Size:** ~500KB (Python source code)
**Dependencies:** 5 Python packages (auto-installed by script)

**System Components:**
- Agent Messaging System (17 files)
- RAG System (10 files)
- Configuration files (auto-created)
- Test scripts (auto-created)

---

## Support & Help

If you get stuck:

1. **First:** Check `AGENT_COMMUNICATION_SYSTEM_MIGRATION_GUIDE.md` → Troubleshooting
2. **Second:** Run verification manually:
   ```bash
   python -c "from agent_messaging import AgentMessenger; print('OK')"
   ```
3. **Third:** Check the Quick Reference for common commands

---

## Migration Checklist

Before you start:
- [ ] Read SIMPLE_MIGRATION_INSTRUCTIONS.md
- [ ] Verify Python 3.10+ is installed: `python3 --version`
- [ ] Choose destination directory
- [ ] Have access to source files

During migration:
- [ ] Run migrate_agent_system.sh OR copy files manually
- [ ] Install Python dependencies
- [ ] Create configuration files
- [ ] Run test scripts

After migration:
- [ ] WebSocket server starts successfully
- [ ] Test message sends/receives correctly
- [ ] All imports work: `python -c "from agent_messaging import AgentMessenger"`

---

## Questions?

- **What is this system?** → Read "How It Works" in SIMPLE_MIGRATION_INSTRUCTIONS.md
- **How long will it take?** → 15-30 minutes with automation, 30-60 minutes manually
- **What if something breaks?** → Check Troubleshooting section in main guide
- **Do I need all files?** → Yes, all 27 files are required for full functionality
- **Can I use just WebSocket?** → Yes, but Letta/RAG fallbacks won't work

---

## Migration Package Version

- **Version:** 1.0
- **Date:** December 14, 2025
- **Source:** /home/adamsl/planner/
- **System:** Agent-to-Agent Communication with WebSocket/Letta/RAG fallback
- **Python:** 3.10+ required

---

## Final Notes

This migration package is designed to be:
- ✅ Simple enough for beginners
- ✅ Detailed enough for experts
- ✅ Automated for speed
- ✅ Manual for control

Choose the approach that fits your needs and skill level.

**Good luck with your migration!**
