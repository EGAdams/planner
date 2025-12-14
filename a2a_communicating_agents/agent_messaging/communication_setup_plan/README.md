# Agent Communication System - Setup Package

This directory contains everything needed to set up the agent communication system in a new location.

## Quick Start

**Easiest Way (Automated):**
```bash
# Copy this entire directory to where you want the system
cp -r communication_setup_plan /your/destination/

# Go there
cd /your/destination/communication_setup_plan

# Run the setup script (installs to current directory)
./migrate_agent_system.sh
```

## What's Included

| File | Purpose |
|------|---------|
| `migrate_agent_system.sh` | Automated setup script (recommended) |
| `SIMPLE_MIGRATION_INSTRUCTIONS.md` | Quick start guide |
| `AGENT_COMMUNICATION_SYSTEM_MIGRATION_GUIDE.md` | Complete documentation |
| `MIGRATION_QUICK_REFERENCE.txt` | File paths and commands |
| `MIGRATION_PACKAGE_README.md` | Guide to using these documents |

## Which Document Should I Use?

- **Want it done fast?** → Run `./migrate_agent_system.sh`
- **Want simple instructions?** → Read `SIMPLE_MIGRATION_INSTRUCTIONS.md`
- **Need complete details?** → Read `AGENT_COMMUNICATION_SYSTEM_MIGRATION_GUIDE.md`
- **Just need file paths?** → Check `MIGRATION_QUICK_REFERENCE.txt`

## What Gets Installed

- **27 Python files** (agent communication system)
- **Python virtual environment** (isolated dependencies)
- **5 Python packages** (websockets, letta-client, chromadb, pydantic, rich)
- **Configuration files** (.env, setup.py, requirements.txt)
- **Test scripts** (verify everything works)

## System Requirements

- Python 3.10 or higher
- 500KB disk space (for source files)
- ~200MB for Python packages

## Time Needed

- Automated: 15-20 minutes
- Manual: 30-60 minutes

## Support

If something doesn't work:
1. Check `AGENT_COMMUNICATION_SYSTEM_MIGRATION_GUIDE.md` → Troubleshooting section
2. Run: `python -c "from agent_messaging import AgentMessenger; print('OK')"`
3. Verify virtual environment is activated: `source venv/bin/activate`

---

**Ready to start?** Run `./migrate_agent_system.sh`
