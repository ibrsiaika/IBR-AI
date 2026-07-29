# IBR Platform — Testing Strategy

**Version**: 0.1.0
**Audience**: QA engineers, developers
**Reference**: PRD Section 41

## Test Pyramid

| Layer | Count Target | Runtime | Coverage | Runs On |
|-------|-------------|---------|----------|---------|
| Unit | 5000+ | <60s | >80% line | Every commit |
| Integration | 500+ | <10min | All contracts | Every commit |
| End-to-End | 100+ | <60min | All user stories | Daily + pre-release |
| Performance | 50+ | <2hr | All NFR targets | Weekly + pre-release |
| Security | 30+ | <4hr | OWASP Top 10 | Weekly + pre-release |
| Load | 10+ | <8hr | 2x peak | Monthly + pre-release |
| Regression | 200+ | <30min | Bug fixes | Every commit |

## Current Status

- **536+ unit tests** — all passing
- **0 lint errors** (ruff)
- **0 type errors** (mypy strict)
- **0 security issues** (bandit)

## Running Tests

```bash
# All unit tests
make test-unit

# With coverage
make test-cov

# Specific module
pytest tests/unit/test_memory_system.py -v

# Performance benchmarks
make test-perf

# Security tests
make test-security
```

## Test Naming Convention

- Unit: `tests/unit/test_<module>.py`
- Integration: `tests/integration/test_<component>_<scenario>.py`
- E2E: `tests/e2e/test_<user_story>.py`
- Performance: `tests/perf/bench_<benchmark>.py`
- Security: `tests/security/test_<owasp_risk>.py`

## Quality Gates

Before any commit is accepted:
- [ ] All tests pass (`make test-unit`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make type-check`)
- [ ] Security scan passes (`make security-check`)
- [ ] Coverage ≥ 80% (`make test-cov`)
- [ ] No secrets in code
- [ ] Documentation updated
