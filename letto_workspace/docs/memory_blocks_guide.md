# Memory Blocks Guide

## Overview

Memory blocks are specialized artifact types that capture different kinds of knowledge. Each block type is optimized for specific use cases and gets ranked with time-decay + relevance.

## Available Memory Blocks

### **1. Error Tracking**
```bash
python main.py artifact \
  "TypeError: Cannot read property 'on' of undefined" \
  error \
  pytest \
  --file-path="path/to/file.py" \
  --project="my_project"
```
**When to use:** Log exceptions, stack traces, test failures

### **2. Fix Documentation**
```bash
python main.py artifact \
  "Fixed by implementing EventEmitter interface" \
  fix \
  manual \
  --file-path="path/to/file.py"
```
**When to use:** Document solutions after fixing bugs

### **3. Design Decisions**
```bash
python main.py artifact \
  "Decision: Using SQLite for simplicity, under 1000 records" \
  decision \
  review \
  --project="my_project"
```
**When to use:** PR rationale, architectural choices, "why we chose X"

### **4. Code Gotchas** ⭐ NEW
```bash
python main.py gotcha \
  "ChromaDB requires \$and operator for multiple filters" \
  "Use {'\$and': [{'a': '1'}, {'b': '2'}]} syntax" \
  --file-path="path/to/file.py"
```
**When to use:** Tricky API behaviors, common mistakes, non-obvious quirks

### **5. Performance Issues** ⭐ NEW
```bash
python main.py perf \
  "Query taking too long on large transactions table" \
  query_time_ms \
  2500 \
  1000 \
  --file-path="path/to/query.py"
```
**When to use:** Slow queries, memory spikes, performance bottlenecks

### **6. Dependency Issues** ⭐ NEW
```bash
python main.py dependency \
  numpy \
  "Version 2.0 breaks chromadb - np.float_ removed" \
  --resolution="Downgrade to numpy<2.0"
```
**When to use:** Version conflicts, breaking changes, compatibility issues

### **7. Deployments** ⭐ NEW
```bash
python main.py deploy \
  "v1.2.0 release" \
  "Deployed artifact memory system to prod" \
  --environment="production" \
  --rollback-info="git checkout v1.1.0 && deploy"
```
**When to use:** Track deployments, rollbacks, production changes

### **8. Test Failures**
```bash
python main.py artifact \
  "test_parser fails: AssertionError at line 45" \
  test_failure \
  ci \
  --project="my_project"
```
**When to use:** CI/CD test failures, integration test issues

### **9. CI/CD Logs**
```bash
python main.py artifact \
  "$(cat build_output.log)" \
  ci_output \
  github_actions \
  --project="my_project"
```
**When to use:** Build failures, CI pipeline issues

### **10. PR Notes**
```bash
python main.py artifact \
  "Reviewer suggested refactoring to async pattern - approved" \
  pr_notes \
  review \
  --project="my_project"
```
**When to use:** Code review feedback, PR discussions

## Searching Memory Blocks

### Basic Search
```bash
# Search across all blocks
python main.py search-artifacts "parser error"

# Returns all relevant blocks, ranked by:
# - Semantic similarity (70%)
# - Recency (25% - newer = higher)
# - Tag boost (10% for error/fix/decision/test_failure)
```

### Filtered Search
```bash
# Only gotchas
python main.py search-artifacts "chromadb" --artifact-type="gotcha"

# Only in specific file
python main.py search-artifacts "query" --file-path="view_transactions.py"

# Performance issues only
python main.py search-artifacts "slow" --artifact-type="slow_query"
```

## Complete Block Type Reference

| Block Type | CLI Command | Boost Priority | Use Case |
|------------|-------------|----------------|----------|
| `error` | `artifact` | ✅ High (+10%) | Exceptions, stack traces |
| `fix` | `artifact` | ✅ High (+10%) | Bug solutions |
| `decision` | `artifact` | ✅ High (+10%) | Design rationale |
| `test_failure` | `artifact` | ✅ High (+10%) | Test failures |
| `gotcha` | `gotcha` | Normal | API quirks, common mistakes |
| `workaround` | `artifact` | Normal | Temporary solutions |
| `slow_query` | `perf` (auto) | Normal | Database performance |
| `memory_spike` | `perf` (auto) | Normal | Memory issues |
| `performance_log` | `perf` (auto) | Normal | General performance |
| `dependency_issue` | `dependency` | Normal | Version conflicts |
| `version_conflict` | `artifact` | Normal | Package incompatibilities |
| `breaking_change` | `artifact` | Normal | API breaking changes |
| `deployment_note` | `deploy` | Normal | Deployment logs |
| `rollback` | `deploy` (auto) | Normal | Production rollbacks |
| `config_change` | `artifact` | Normal | Configuration updates |
| `ci_output` | `artifact` | Normal | CI/CD logs |
| `pr_notes` | `artifact` | Normal | Code review feedback |
| `runlog` | `artifact` | Normal | Command outputs |
| `anti_pattern` | `artifact` | Normal | Bad practices to avoid |
| `best_practice` | `artifact` | Normal | Recommended patterns |

## Real-World Workflows

### **Workflow 1: Debug Loop**
```bash
# 1. Hit error
python main.py artifact "Error message" error pytest --file-path="foo.py"

# 2. Try solution, document as fix
python main.py artifact "Applied fix XYZ" fix manual --file-path="foo.py"

# 3. If you discover a gotcha
python main.py gotcha \
  "Library requires init before use" \
  "Call .initialize() in constructor" \
  --file-path="foo.py"

# 4. Later, search for similar issues
python main.py search-artifacts "similar error keywords"
```

### **Workflow 2: Performance Monitoring**
```bash
# Log slow query from monitoring
python main.py perf \
  "Users endpoint timeout" \
  response_time_ms \
  5000 \
  2000 \
  --file-path="api/users.py"

# Search for performance issues later
python main.py search-artifacts "timeout" --artifact-type="slow_query"
```

### **Workflow 3: Dependency Management**
```bash
# Log breaking change
python main.py dependency \
  pydantic \
  "v2.0 breaks BaseModel.parse_obj()" \
  --resolution="Use model_validate() instead"

# When you hit similar issue
python main.py search-artifacts "pydantic" --artifact-type="dependency_issue"
```

### **Workflow 4: Deployment Tracking**
```bash
# Log deployment
python main.py deploy \
  "v2.0.0" \
  "Major refactor: switched to async DB layer" \
  --environment="production" \
  --rollback-info="docker compose down && git checkout v1.9.0 && docker compose up"

# If issues occur, log rollback
python main.py deploy \
  "Rollback to v1.9.0" \
  "Async layer causing connection leaks" \
  --environment="production" \
  --rollback-info="Fixed in v2.0.1"

# Review deployment history
python main.py search-artifacts "deployment" --artifact-type="deployment_note"
```

## Automatic Integration

### Pre-commit Hook (Log Errors)
```bash
# .git/hooks/pre-commit
#!/bin/bash
if ! pytest tests/ 2>&1 | tee test_output.log; then
  python main.py artifact \
    "$(cat test_output.log)" \
    test_failure \
    pre_commit \
    --project="$(basename $PWD)"
fi
```

### CI/CD Integration
```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest tests/
  continue-on-error: true

- name: Log test failures
  if: failure()
  run: |
    python main.py artifact \
      "$(cat pytest_output.txt)" \
      test_failure \
      github_actions \
      --project="${{ github.repository }}"
```

### Performance Monitoring Script
```python
# monitor_performance.py
import time
from rag_system.core.document_manager import DocumentManager

dm = DocumentManager()

def log_slow_query(query_name, duration_ms, threshold=1000):
    if duration_ms > threshold:
        dm.log_performance_issue(
            description=f"{query_name} exceeded threshold",
            metric="query_time_ms",
            value=duration_ms,
            threshold=threshold,
            file_path=f"queries/{query_name}.py"
        )

# Use in your code
start = time.time()
result = expensive_query()
duration = (time.time() - start) * 1000
log_slow_query("user_transactions", duration)
```

## Advanced: Creating Custom Memory Blocks

### 1. Add New Artifact Type
```python
# rag_system/models/document.py
class ArtifactType(str, Enum):
    # ... existing types ...
    SECURITY_ALERT = "security_alert"
    API_CHANGE = "api_change"
```

### 2. Create Helper Method
```python
# rag_system/core/document_manager.py
def log_security_alert(self, threat: str, severity: str,
                       mitigation: str, **kwargs) -> str:
    artifact_text = f"**Threat**: {threat}\n**Severity**: {severity}\n**Mitigation**: {mitigation}"
    return self.add_runtime_artifact(
        artifact_text=artifact_text,
        artifact_type="security_alert",
        source="security_scan",
        tags=["security", severity],
        **kwargs
    )
```

### 3. Add CLI Command
```python
# main.py
@app.command()
def security(threat: str, severity: str, mitigation: str):
    """Log a security alert"""
    dm, _ = get_managers()
    doc_id = dm.log_security_alert(threat, severity, mitigation)
    console.print(f"🔒 Security alert logged! ID: {doc_id}")
```

## Tips & Best Practices

### ✅ **DO**
- Log errors immediately when they occur
- Include file paths for code-specific issues
- Add resolution when logging dependency issues
- Use gotchas for non-obvious API behaviors
- Log deployments before and after (for rollback tracking)

### ❌ **DON'T**
- Don't log sensitive data (passwords, API keys, PII)
- Don't log extremely long outputs (truncate to ~1000 chars)
- Don't duplicate - search first to see if issue already logged
- Don't forget project names for multi-project repos

## Memory Block Ranking

All blocks are ranked using:
```
score = (semantic_similarity * 0.70) + (recency * 0.25) + tag_boost

where:
  semantic_similarity = ChromaDB vector distance
  recency = exp(-0.1 * days_old / 7)  # decays over time
  tag_boost = +0.10 for high-priority types (error/fix/decision/test_failure)
```

**Result:** Recent, relevant, high-priority blocks appear first!

---

**Status:** ✅ All memory blocks tested and working
**Storage:** ChromaDB at `./storage/chromadb/`
**View Stats:** `python main.py status`
