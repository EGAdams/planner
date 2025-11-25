# A2A System - Quick Reference Card

**Last Updated**: 2025-11-24T20:48:00-05:00

---

## System Status: ✅ OPERATIONAL

| Service | Port | PID | URL |
|---------|------|-----|-----|
| Letta Server | 8283 | 897344 | http://localhost:8283 |
| Dashboard UI | 3000 | 897410 | http://localhost:3000 |
| Orchestrator Agent | - | 897360 | - |
| Dashboard Agent | - | 897375 | - |

---

## Quick Commands

```bash
# Start system
./start_a2a_system.sh

# Stop system
./stop_a2a_system.sh

# Check status
ps -p $(cat logs/a2a_system.pids | cut -d: -f2 | tr '\n' ',')

# View logs
tail -f logs/*.log

# Health check
curl http://localhost:8283/ && curl http://localhost:3000/
```

---

## Recent Issues Fixed

1. ✅ Duplicate dashboard agent processes - RESOLVED
2. ✅ ChromaDB database corruption - RESOLVED (backup: chromadb.corrupted.20251124_204738)
3. ⚠️ Google Gemini API quota - DOCUMENTED (requires user action)

---

## Known Limitations

- **API Quota**: Orchestrator uses Google Gemini free tier (200 requests/day)
  - If exhausted, wait for reset, upgrade plan, or switch providers
  - Check quota: https://ai.dev/usage?tab=rate-limit

---

## Quick Troubleshooting

**Services won't start?**
```bash
# Check ports
lsof -i :8283 && lsof -i :3000
# Kill if needed
lsof -ti:8283 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

**ChromaDB errors?**
```bash
# Backup and reset
./stop_a2a_system.sh
mv storage/chromadb "storage/chromadb.backup.$(date +%Y%m%d_%H%M%S)"
./start_a2a_system.sh
```

**Duplicate processes?**
```bash
# Full restart
./stop_a2a_system.sh
sleep 3
./start_a2a_system.sh
```

---

## Documentation Files

- `handoff.md` - Comprehensive handoff notes
- `SYSTEM_REPAIR_COMPLETE.md` - Detailed repair report
- `RESTART_INSTRUCTIONS.md` - Restart procedures
- `REPAIR_SUMMARY.txt` - Executive summary
- `QUICK_REFERENCE.md` - This file

---

## Next Steps

1. (Optional) Resolve API quota issue for orchestrator
2. Test agent communication
3. Verify memory persistence
4. Add more specialized agents

---

**System is ready for productive use!** 🚀
