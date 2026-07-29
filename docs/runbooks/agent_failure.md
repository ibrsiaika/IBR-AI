# IBR Platform — Runbook: Agent Failure

**Trigger**: Agent health_check returns "unhealthy" or agent execution fails.

## Symptoms
- Agent.execute() raises AgentExecutionError
- Agent.health_check() returns status="unhealthy"
- TaskOrchestrator reports failed request

## Investigation Steps

1. Check agent status:
```python
from ibr_platform.agents.lifecycle import AgentLifecycle
lc = AgentLifecycle()
info = lc.get_info(agent_id)
print(info)  # Check status, tasks_completed, tasks_failed
```

2. Check orchestrator health:
```bash
curl http://localhost:8000/api/v1/orchestrator/health
```

3. Check memory stats:
```bash
curl http://localhost:8000/api/v1/memory/stats
```

## Resolution

### If agent is unhealthy:
1. Terminate the agent: `await lc.terminate(agent_id)`
2. Spawn a new instance: `await lc.spawn("agent_name", AgentClass, config={})`
3. Verify health: `await lc.health_check(new_agent_id)`

### If task failed:
1. Check the task's error message in the AgentResult
2. If knowledge gap: re-run ResearchPipeline to gather more data
3. If reasoning error: retry with different planning paradigm
4. If calibration error: run EvaluationAgent to recalibrate

### If memory is full:
1. Clear working memory: `await mgr.clear_tier(MemoryTier.WORKING)`
2. Evict expired: `await mgr.evict_expired()`
3. Compress old entries: `await mgr.summarize(old_entry_ids)`

## Escalation
- If issue persists after 3 retries: escalate to engineering lead
- If data loss suspected: check audit log integrity: `log.verify_integrity()`
- If security incident: activate incident response plan
