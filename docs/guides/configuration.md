# IBR Platform — Configuration Guide

**Version**: 0.1.0

## Configuration Methods

### 1. Environment Variables (prefix: IBR_)

```bash
export IBR_DEPLOYMENT_MODE=enterprise
export IBR_RAM_BUDGET_MB=131072
export IBR_MAX_CONCURRENT_AGENTS=100
export IBR_ENABLE_GPU=true
export IBR_ENABLE_TRAINING=true
```

### 2. YAML Config File

```python
from ibr_platform.config import Settings
settings = Settings.from_yaml("configs/enterprise.yaml")
```

Example YAML (`configs/enterprise.yaml`):
```yaml
deployment_mode: enterprise
ram_budget_mb: 131072
max_concurrent_agents: 100
enable_training: true
enable_gpu: true
enable_distributed: true

database:
  sql_backend: postgresql
  sql_url: postgresql://user:pass@db:5432/ibr
  vector_backend: qdrant
  vector_url: http://qdrant:6333
  graph_backend: neo4j
  graph_url: bolt://neo4j:7687

security:
  audit_log_enabled: true
  sandbox_enabled: true

model:
  default_model: deepseek-v3
  inference_engine: vllm
  gpu_enabled: true
```

### 3. Python Code

```python
from ibr_platform.config import Settings, DeploymentMode

settings = Settings(
    deployment_mode=DeploymentMode.TINY,
    ram_budget_mb=2048,
)
```

## Deployment Mode Defaults

| Mode | RAM | Agents | GPU | Training | Distributed |
|------|-----|--------|-----|----------|-------------|
| Tiny | 2GB | 1 | No | No | No |
| Compact | 8GB | 5 | No | Yes | No |
| Professional | 32GB | 20 | Yes | Yes | No |
| Enterprise | 128GB+ | 100 | Yes | Yes | Yes |
