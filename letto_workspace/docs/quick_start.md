# Memory Block Agent - Quick Start

## 🚀 Installation

```bash
# 1. Install Letta
pip install letta

# 2. Launch Letta Agent IDE
letta run

# 3. Import the agent file
# In Letta IDE: Import → Select memory_block_agent.af
```

## 💬 Example Conversations

### Search for Past Issues
```
You: Search for parser errors
Agent: [searches memory blocks with time-decay ranking]
Agent: Found 2 results:
  1. TypeError: parser.on is not a function (score: 0.89)
  2. Fixed by implementing EventEmitter (score: 0.85)
```

### Log an Error
```
You: Log this error: "TypeError in parsers.py line 145"
Agent: [creates error artifact]
Agent: ✅ Error logged! You can search for it later with "parser TypeError"
```

### Log a Gotcha
```
You: ChromaDB requires $and operator for multiple filters
Agent: What's the workaround?
You: Use {'$and': [{'a': '1'}, {'b': '2'}]} syntax
Agent: [logs gotcha with workaround]
```

### Find Performance Issues
```
You: Show me slow queries
Agent: [searches with artifact_type=slow_query]
Agent: Found 3 slow queries in the last week...
```

### Log a Deployment
```
You: Deployed v1.2.0 to production
Agent: [logs deployment artifact with timestamp]
```

## 🛠️ Available Commands

| What to Say | What Happens |
|-------------|--------------|
| "Search for X" | Semantic search with time-decay |
| "Log this error: X" | Creates error artifact |
| "Log this fix: X" | Creates fix artifact |
| "Log gotcha: X, workaround: Y" | Creates gotcha artifact |
| "Query taking Xms, threshold Yms" | Logs performance issue |
| "Package X has issue Y" | Logs dependency issue |
| "Deployed X to Y" | Logs deployment |
| "Show recent errors" | Searches error artifacts |
| "Find issues in file.py" | Searches by file path |

## 📊 Memory Block Types

**Ask the agent to log these types:**

| Type | Example |
|------|---------|
| error | "TypeError: cannot read property 'on'" |
| fix | "Fixed by implementing EventEmitter" |
| decision | "Using SQLite for simplicity" |
| gotcha | "API requires initialization before use" |
| slow_query | "Query taking 2500ms" |
| dependency_issue | "numpy 2.0 breaks chromadb" |
| deployment_note | "Deployed v1.2.0 to prod" |

## 🎯 Pro Tips

1. **Always search first** - Agent automatically searches before logging
2. **Be specific** - Include file paths and project names
3. **Recent = Relevant** - Newer blocks rank higher (time-decay)
4. **Tag boost** - errors, fixes, decisions get +10% ranking
5. **Natural language** - Describe problems naturally, agent understands

## 🔗 Integration with CLI

**Both work together:**

Via Agent:
```
You: "Search for chromadb errors"
Agent: [uses tool search_artifacts]
```

Via CLI:
```bash
python main.py search-artifacts "chromadb"
```

Same ChromaDB storage = Same results! 🎉

## 📝 Quick Examples

### Debug Loop
```
You: Getting parser error
Agent: [searches] Found similar error from 2 days ago
Agent: Past fix: implement EventEmitter interface
You: That worked! Log it
Agent: [logs fix]
```

### Performance Tracking
```
You: Query timeout on users endpoint
Agent: [searches slow queries] No similar issues found
You: Log it: 5000ms, threshold 2000ms
Agent: [logs performance issue]
```

### Dependency Hell
```
You: numpy 2.0 breaks chromadb
Agent: [searches] Found similar from last week
Agent: Resolution: downgrade to numpy<2.0
```

## 🚨 Common Questions

**Q: How do I see all memory blocks?**
A: "Show me recent artifacts" or use CLI: `python main.py status`

**Q: Can I filter by file?**
A: "Find issues in parsers.py"

**Q: How far back does search go?**
A: All history, but older items rank lower (time-decay)

**Q: Can I edit memory blocks?**
A: Yes! In Letta IDE, view and edit the agent's memory

**Q: How do I export my work?**
A: Letta IDE → Export Agent → Save .af file

## 📚 Full Documentation

- Detailed guide: `letto_workspace/README.md`
- All artifact types: `MEMORY_BLOCKS_GUIDE.md`
- Technical details: `LETTA_INTEGRATION.md`

---

**Ready to start?** Import `memory_block_agent.af` into Letta IDE! 🎉
