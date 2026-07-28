# IBR Platform — Deployment Guide

**Version**: 0.1.0
**Audience**: DevOps, infrastructure engineers

## Deployment Modes

### Tiny Mode (Laptop)
```bash
export IBR_DEPLOYMENT_MODE=tiny
python -m ibr_platform.api.server --host 0.0.0.0 --port 8000
```
- RAM: 2 GB budget
- Model: 125M-1B (Llama 3.2 1B in GGUF Q4_K_M)
- Engine: llama.cpp
- No GPU required

### Compact Mode (Workstation)
```bash
export IBR_DEPLOYMENT_MODE=compact
python -m ibr_platform.api.server --host 0.0.0.0 --port 8000
```
- RAM: 8 GB budget
- Model: 1B-3B (Phi-3 Mini)
- Engine: llama.cpp or vLLM
- Optional: consumer GPU

### Professional Mode (Server)
```bash
export IBR_DEPLOYMENT_MODE=professional
python -m ibr_platform.api.server --host 0.0.0.0 --port 8000
```
- RAM: 32 GB budget
- Model: 7B-13B (Mistral 7B in INT8)
- Engine: vLLM with FlashAttention
- GPU: 1-4 datacenter GPUs

### Enterprise Mode (Cluster)
```bash
export IBR_DEPLOYMENT_MODE=enterprise
# Deploy via Helm
helm install ibr-platform ./infra/helm/ -f configs/enterprise.yaml
```
- RAM: 128+ GB budget
- Model: 70B+ or MoE (DeepSeek-V3)
- Engine: vLLM with tensor parallelism
- GPU: 8-256 GPUs

## Docker

```bash
# Build
docker build -t ibr-platform:latest .

# Run
docker run -p 8000:8000 -p 9090:9090 ibr-platform:latest
```

## Health Check

```bash
curl http://localhost:8000/health
# {"status": "healthy", "version": "0.1.0"}
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI spec: http://localhost:8000/openapi.json
