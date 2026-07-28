# IBR PLATFORM — MASTER BUILD PROMPT FOR AI ENGINEERING AGENT
# Version: 1.0 | Length: 1100+ lines | Purpose: Complete project implementation
# Read this ENTIRE prompt before writing a single line of code.

================================================================================
SECTION 0: ABSOLUTE RULES — NON-NEGOTIABLE
================================================================================

RULE #1: READ THE PDF FIRST, COMPLETELY
Before writing ANY code, you MUST read the entire PDF at:
/home/z/my-project/download/IBR_Platform_PRD.pdf (224 pages, 107 sections, 6 parts)
Do NOT skip sections. Do NOT skim. Read every section, every table, every citation.
If you cannot access the PDF, STOP and ask the user. Do NOT proceed with assumptions.
The PDF is the SINGLE SOURCE OF TRUTH. All requirements are there.

RULE #2: ONE SECTION AT A TIME
You will work on ONE section at a time. Not two. Not three. ONE.
Complete that section FULLY before moving to the next.
"Fully" means: code written, tests passing, documentation updated, committed to git.
A section is NOT complete until ALL of its acceptance criteria are met.
Do NOT start Section N+1 until Section N is fully complete and committed.

RULE #3: TESTS BEFORE CODE
For every section, BEFORE writing implementation code:
1. Write test cases based on the section's acceptance criteria
2. Run the tests (they will fail — that's expected, no implementation yet)
3. THEN write the implementation
4. Run the tests again until they pass
This is Test-Driven Development (TDD). No exceptions.

RULE #4: RESEARCH BEFORE IMPLEMENTATION
For every section, BEFORE writing code:
1. Search the web for the latest (2025-2026) best practices for that section's topic
2. Read at least 3 authoritative sources (arXiv papers, official docs, vendor blogs)
3. Document your findings in a research note (docs/research/section_NN_research.md)
4. Cite every source with URL and publication date
Do NOT fabricate research. If you cannot verify a claim, mark it as "unverified".
Do NOT skip this step. Implementation without research produces outdated code.

RULE #5: NO SHORTCUTS, NO STUBS, NO "TODO LATER"
Every function must be fully implemented. No `pass` statements. No `// TODO`. No stubs.
If a function is too complex to implement in one pass, break it into smaller functions.
But every function must WORK. Every test must PASS. Every feature must be COMPLETE.
"Good enough for now" is NOT acceptable. "I'll fix it later" is NOT acceptable.

RULE #6: CONVENTIONAL COMMITS
Every git commit must follow Conventional Commits format:
  type(scope): description
Types: feat, fix, docs, style, refactor, test, chore, perf, ci
Scope: platform, agents, api, dashboard, infra, docs, tests
Example: feat(agents): add verification agent with contradiction detection
Commit body must explain WHAT and WHY (not HOW — the diff shows how).
Reference the section number: "Implements Section 33 (Phase 3 — Agent Framework)"

RULE #7: NEVER PUSH WITHOUT USER APPROVAL
You MUST NOT push to GitHub without explicit user approval.
Before every push, display:
  - Commit summary (commits to be pushed)
  - Changed files (with diff stats)
  - Test results (latest CI run)
  - Documentation status
  - Unresolved issues
Wait for the user to type "PUSH APPROVED" before executing `git push`.
If the user says anything else, do NOT push. Address their concern first.

RULE #8: SECURITY-FIRST
- Never hardcode secrets, tokens, passwords, or API keys in source code
- Never commit .env files, credentials.json, or any secrets file
- Always use environment variables or a secrets manager (HashiCorp Vault)
- The .gitignore MUST exclude: .env, *.key, *.pem, credentials/, secrets/
- If you accidentally commit a secret, STOP, alert the user immediately,
  and help them rotate the secret before proceeding

RULE #9: CPU-FIRST DESIGN
Every component must run on commodity CPU hardware.
GPU acceleration is OPTIONAL — never make it mandatory.
Test every component on CPU before claiming it works.
If a component requires GPU, document the requirement clearly and
provide a CPU fallback (even if slower).

RULE #10: DOCUMENTATION IS NOT OPTIONAL
Every module, every function, every class must have:
- A docstring explaining what it does, its parameters, and its return value
- Type hints (Python) or TypeScript types
- Usage example in the docstring
- Link to the relevant PRD section
Documentation is written BEFORE implementation, not after.

RULE #11: NO DUPLICATION (DRY)
If you find yourself writing similar code in two places, extract it into a
shared function/module. The knowledge graph is the single source of truth
for facts. The model registry is the single source of truth for models.
The memory system is the single source of truth for state.
Do NOT create parallel implementations of the same concept.

RULE #12: OBSERVABILITY FROM DAY ONE
Every component must emit structured logs (JSON), metrics (Prometheus format),
and traces (OpenTelemetry). No component is "done" until it is observable.
Logs go to stdout (collected by Docker/Kubernetes).
Metrics are exposed at /metrics endpoint.
Traces are exported to Jaeger/Tempo.

================================================================================
SECTION 1: PROJECT OVERVIEW
================================================================================

You are building the IBR (Intelligent Brain Runtime) Platform — an autonomous
agentic AI research and self-improving foundation model platform.

The complete specification is in:
/home/z/my-project/download/IBR_Platform_PRD.pdf

The PDF contains 6 parts, 107 sections:
- Part I (Sections 1-29): Product Requirements Document
- Part II (Sections 30-44): Phase-by-Phase Engineering Specifications (Phases 0-13)
- Part III (Sections 45-59): Verified Research on Compression & Golden Tokens
- Part IV (Sections 60-75): Extended Research on Protocols & Infrastructure
- Part V (Sections 76-91): Empirical Tests & CS Formulas
- Part VI (Sections 92-107): Claude, Compact Models, Data Optimization

The platform has:
- 29+ specialized AI agents (Planner, Research, Verification, Memory, etc.)
- Multi-tier memory system (working, short-term, long-term, semantic, etc.)
- Knowledge graph (Neo4j) for verified facts
- Vector database (Qdrant or pgvectorscale) for similarity search
- Training pipeline (SFT, LoRA, QLoRA, GRPO, distillation)
- Evaluation harness (MMLU, GPQA, HumanEval, custom benchmarks)
- Self-improvement loop with human approval gates
- Production deployment with canary, A/B, automatic rollback
- 4 deployment modes: Tiny (laptop), Compact (workstation),
  Professional (server), Enterprise (cluster)

================================================================================
SECTION 2: PREREQUISITES — ENVIRONMENT SETUP
================================================================================

Before starting ANY implementation, verify the environment:

2.1. Python 3.11+ installed (run: python3 --version)
2.2. Node.js 20+ installed (run: node --version)
2.3. Docker installed (run: docker --version)
2.4. Kubernetes CLI installed (run: kubectl version --client)
2.5. Git installed and configured (run: git config --global user.name; git config --global user.email)
2.6. The PDF is accessible at /home/z/my-project/download/IBR_Platform_PRD.pdf
2.7. The benchmark scripts are accessible at:
     - /home/z/my-project/scripts/run_benchmarks.py
     - /home/z/my-project/scripts/run_benchmarks_part6.py
2.8. The research JSON files are accessible at /home/z/my-project/research/*.json

If ANY prerequisite is missing, STOP and ask the user to install it.
Do NOT proceed with workarounds.

2.9. Create the project structure:
  /home/z/my-project/ibr-platform/
    ├── platform/           # Core platform code
    ├── agents/             # Agent implementations
    ├── api/                # API definitions (OpenAPI, gRPC)
    ├── dashboard/          # Next.js web dashboard
    ├── infra/              # Kubernetes, Helm, Terraform
    ├── docs/               # Documentation
    │   ├── adr/            # Architecture Decision Records
    │   ├── research/       # Research notes per section
    │   └── guides/         # Developer/deployment guides
    ├── tests/              # Test suites
    ├── scripts/            # Build/release scripts
    ├── .gitignore
    ├── README.md
    ├── pyproject.toml      # Python project config
    ├── package.json        # Node.js project config (for dashboard)
    └── Makefile            # Common commands

2.10. Initialize git in the project directory:
  cd /home/z/my-project/ibr-platform
  git init
  git add .gitignore README.md
  git commit -m "chore: initialize IBR Platform repository"

================================================================================
SECTION 3: WORKFLOW — HOW TO PROCESS EACH PRD SECTION
================================================================================

For EACH section in the PRD (Sections 1-107), follow this EXACT workflow:

STEP 1: READ THE SECTION
- Open the PDF
- Read the section completely (all subsections, tables, citations)
- Re-read it if anything is unclear
- Note the section's: objectives, deliverables, acceptance criteria, dependencies

STEP 2: RESEARCH
- Identify the section's key technical topic
- Search the web for 2025-2026 best practices on that topic
- Read at least 3 authoritative sources
- Write a research note: docs/research/section_NN_research.md
- The research note must include:
  - Topic summary
  - Sources (with URLs and dates)
  - Key findings
  - How findings apply to this section
  - Any deviations from the PRD (with justification)

STEP 3: WRITE TESTS (TDD)
- Based on the section's acceptance criteria, write test cases
- Tests go in: tests/test_section_NN_*.py
- Tests must cover:
  - Happy path (normal operation)
  - Error paths (invalid input, missing data, network failure)
  - Edge cases (empty input, boundary values, concurrent access)
  - Performance (latency, throughput targets from PRD)
- Run the tests: pytest tests/test_section_NN_*.py
- They will FAIL (no implementation yet) — this is expected

STEP 4: WRITE IMPLEMENTATION
- Implement the section's functionality
- Code goes in the appropriate module (platform/, agents/, api/, etc.)
- Follow the architecture in PRD Section 10 (layered architecture)
- Apply the patterns from PRD Sections 57, 74, 107 (50 patterns)
- Use the verified techniques from PRD Sections 45-107
- Write docstrings for every function/class
- Add type hints everywhere

STEP 5: RUN TESTS UNTIL THEY PASS
- Run: pytest tests/test_section_NN_*.py
- Fix failures one by one
- Do NOT move on until ALL tests pass
- If a test is fundamentally wrong (not just failing), revise the test
  with justification — but never delete a test to make it pass

STEP 6: WRITE DOCUMENTATION
- Update docs/ with:
  - Architecture changes (if any)
  - API reference (if new API)
  - Configuration guide (if new config)
  - Runbook (if new operational procedure)
- Update README.md if the section adds user-visible features

STEP 7: QUALITY GATES
Before committing, verify ALL of the following:
- [ ] All tests pass (pytest tests/ — not just this section's tests)
- [ ] No linting errors (ruff check . for Python, eslint for TypeScript)
- [ ] No type errors (mypy for Python, tsc for TypeScript)
- [ ] No security issues (bandit for Python, npm audit for Node.js)
- [ ] Documentation is updated
- [ ] No secrets in code (grep -r "ghp_\|sk-\|password\|secret" --exclude-dir=.git)
- [ ] Code coverage ≥ 80% for new code (pytest --cov)

If ANY gate fails, fix it before committing. No exceptions.

STEP 8: COMMIT
- Stage changes: git add -A
- Verify what's staged: git status
- Commit with conventional commit format:
  git commit -m "feat(scope): implement section NN — <section title>

  Implements PRD Section NN (<section name>).
  - <key change 1>
  - <key change 2>
  - Tests: <N> tests added, all passing
  - Documentation: <what docs updated>

  Refs: PRD Section NN"
- Do NOT push yet. Pushing requires user approval (RULE #7).

STEP 9: SECTION COMPLETION CHECKLIST
Before moving to the next section, verify:
- [ ] Section's acceptance criteria (from PRD) are ALL met
- [ ] All tests for this section pass
- [ ] All tests for previous sections still pass (no regressions)
- [ ] Documentation is updated
- [ ] Commit is made (but not pushed)
- [ ] Research note is written
- [ ] No TODOs, stubs, or incomplete code

If ANY item is unchecked, the section is NOT complete. Do NOT move on.

================================================================================
SECTION 4: SECTION PRIORITY ORDER
================================================================================

Process sections in this order (NOT numerical order — dependency order):

PHASE 0 — FOUNDATION (do first)
1. Section 32: System Design — Folder Structure & Architecture
2. Section 31: Phase 1 — Deep Research (ADRs for all 14 technology decisions)
3. Section 10: High-Level Architecture (implement layer by layer)
4. Section 11: Multi-Agent Architecture (agent framework base)
5. Section 22: Security & Safety Requirements (security infrastructure)

PHASE 1 — CORE PLATFORM
6. Section 33: Agent Framework (AgentBase, 25+ agents)
7. Section 35: Memory System (12 memory tiers)
8. Section 34: Research Engine (crawlers, parsers, extractors)
9. Section 50: Production RAG (hybrid search, reranking)
10. Section 51: Knowledge Graph Construction

PHASE 2 — TRAINING & EVALUATION
11. Section 39: Model Training (SFT, LoRA, QLoRA, GRPO)
12. Section 38: Dataset Generation (9 dataset types)
13. Section 40: Self-Improvement Loop
14. Section 70: RAG Evaluation (RAGAS, TruLens, DeepEval)
15. Section 67: Model Registry (MLflow 3.0)

PHASE 3 — INFRASTRUCTURE
16. Section 65: GPU Cluster Scheduling (Volcano, KubeRay)
17. Section 66: Cost Optimization (spot instances, routing)
18. Section 100: Low-Resource Inference (llama.cpp, MLC-LLM)
19. Section 47: Golden Token Stack (PagedAttention, speculative decoding)
20. Section 46: Model Compression (INT8, INT4, GGUF)

PHASE 4 — SAFETY & GOVERNANCE
21. Section 54: OWASP Top 10 Compliance
22. Section 64: LLM Guardrails (6-layer stack)
23. Section 94: Constitutional AI & RLAIF
24. Section 23: Human-in-the-Loop & Governance
25. Section 28: Compliance Appendix (GDPR, SOC2, HIPAA)

PHASE 5 — APIs & DASHBOARD
26. Section 20: APIs & Dashboard
27. Section 61: MCP Integration
28. Section 62: Structured Outputs
29. Section 63: Streaming (SSE)
30. Section 68: LLM Observability (LangSmith, Phoenix)

PHASE 6 — OPTIMIZATION
31. Section 95: Phi-3 Textbook Quality Data
32. Section 96: Compact Model Adoption
33. Section 97: Multi-Model Routing
34. Section 101: Complete Golden Token Stack
35. Section 89: CPU-First Deep Dive

PHASE 7 — REMAINING SECTIONS
36-107. All remaining sections in numerical order

NOTE: Within each phase, process sections in the listed order.
Do NOT skip ahead. Each section builds on previous ones.

================================================================================
SECTION 5: DETAILED INSTRUCTIONS PER SECTION TYPE
================================================================================

5.1. AGENT SECTIONS (Sections 11, 12, 33, etc.)
For each agent:
- Create a Python class inheriting from AgentBase
- Implement: initialize(config), execute(task) -> result, health_check() -> status, shutdown()
- Define: role, inputs (typed schema), outputs (typed schema), tools, memory access, permissions
- Implement failure recovery (retry, escalate, degrade)
- Write unit tests for execute() with mocked tools and memory
- Write integration tests with real tools and memory (in Docker)
- Write a runbook: docs/runbooks/agent_<name>.md
- Register the agent in the agent registry
- Add the agent to the dashboard's agent list

5.2. MEMORY SECTIONS (Sections 15, 35, 71)
For each memory tier:
- Implement the storage backend (Redis, Qdrant, Neo4j, PostgreSQL)
- Implement the Memory Agent API (write, read, search, update, delete, summarize)
- Implement scope isolation (project, user, organization)
- Implement versioning (immutable entries, prior versions queryable)
- Implement audit logging (every operation logged)
- Write tests for: CRUD operations, scope isolation, versioning, audit
- Benchmark: latency, throughput, capacity (use scripts/run_benchmarks.py as reference)

5.3. TRAINING SECTIONS (Sections 18, 39, 52)
For each training technique:
- Implement the training pipeline (PyTorch + DeepSpeed)
- Support: config-driven training (YAML configs)
- Implement: checkpointing, resumption, preemption
- Implement: reproducibility (seeded, deterministic where possible)
- Implement: safety evaluation (run before deployment)
- Write tests: training runs to completion, checkpoint/resume works, reproducibility verified
- Benchmark: training throughput, loss convergence

5.4. INFRASTRUCTURE SECTIONS (Sections 17, 37, 65, 100)
For each infrastructure component:
- Write Helm charts (infra/helm/)
- Write Terraform modules (infra/terraform/)
- Write Kubernetes manifests (infra/k8s/)
- Implement health checks (liveness, readiness)
- Implement autoscaling (HPA, KEDA)
- Write deployment guide: docs/guides/deploy_<component>.md
- Test: deploy to local Kind cluster, verify functionality

5.5. API SECTIONS (Sections 20, 61, 62, 63)
For each API:
- Write OpenAPI 3.1 specification (api/openapi/)
- Implement the API (FastAPI for Python)
- Add authentication (OAuth 2.0 / OIDC)
- Add rate limiting (per-tenant, per-API)
- Add audit logging (every state-changing request)
- Write SDK clients (Python, TypeScript, Go)
- Write tests: API contract tests, integration tests, load tests
- Generate API reference docs (Redocly)

5.6. EVALUATION SECTIONS (Sections 19, 40, 70, 58, 75, 90)
For each evaluation:
- Implement the evaluation harness
- Support: standard benchmarks (MMLU, GPQA, HumanEval, etc.)
- Support: custom benchmarks (tenant-specific)
- Implement: statistical significance testing
- Implement: continuous evaluation (daily probe sets)
- Write tests: evaluation runs correctly, scores match expected
- Run the evaluation on a baseline model, record results

5.7. RESEARCH SECTIONS (Sections 31, 45-107)
For each research-backed section:
- Read the cited sources (URLs in the PRD)
- Verify the claims (re-run benchmarks if possible)
- Write an ADR: docs/adr/NNNN-<topic>.md
- The ADR must include: context, decision, alternatives, consequences
- Implement based on the ADR's decision
- If research findings contradict the PRD, document the deviation and
  consult the user before proceeding

================================================================================
SECTION 6: TESTING REQUIREMENTS
================================================================================

6.1. TEST PYRAMID (from PRD Section 41)
- Unit tests: 5000+ tests, <60s total runtime, >80% line coverage
- Integration tests: 500+ tests, <10 min total
- End-to-end tests: 100+ tests, <60 min total
- Performance tests: 50+ tests, <2 hours total
- Security tests: 30+ tests, <4 hours total
- Load tests: 10+ tests, <8 hours total
- Regression tests: 200+ tests, <30 min total

6.2. TEST NAMING CONVENTION
- Unit: tests/unit/test_<module>_<function>.py
- Integration: tests/integration/test_<component>_<scenario>.py
- E2E: tests/e2e/test_<user_story>.py
- Performance: tests/perf/bench_<benchmark>.py
- Security: tests/security/test_<owasp_risk>.py

6.3. TEST DATA
- Use synthetic data for unit tests (fast, deterministic)
- Use realistic data for integration/E2E (from fixtures or generators)
- NEVER use production data in tests
- Anonymize any data that resembles real users

6.4. CONTINUOUS TESTING
- Tests run on every commit (pre-commit hook)
- Tests run on every PR (CI pipeline)
- Tests run nightly (full suite including performance, security, load)
- Test results are tracked over time (regression detection)
- Flaky tests are quarantined within 24 hours

6.5. BENCHMARK VALIDATION
For every benchmark claim in the PRD (Sections 56, 73, 90, 104, 105, 106):
- Implement a test that reproduces the benchmark
- Run the test on the development machine
- Compare results to the PRD's claimed values
- If results differ by >20%, investigate and document
- Save benchmark results to: tests/perf/results/<date>_<benchmark>.json

================================================================================
SECTION 7: DOCUMENTATION REQUIREMENTS
================================================================================

7.1. DOCUMENTATION DELIVERABLES (from PRD Section 42)
- README.md (project overview, quick start)
- Architecture Guide (docs/architecture.md)
- API Reference (generated from OpenAPI)
- Developer Guide (docs/guides/developer.md)
- Deployment Guide (docs/guides/deployment.md)
- Configuration Guide (docs/guides/configuration.md)
- Plugin Guide (docs/guides/plugins.md)
- Training Guide (docs/guides/training.md)
- Troubleshooting Guide (docs/runbooks/)
- Security Guide (docs/security.md)
- Release Notes (CHANGELOG.md)

7.2. DOCUMENTATION STANDARDS
- Every doc starts with: "Who this is for" and "What you will learn"
- Code examples are tested (doctest pattern)
- Diagrams are source-controlled (Mermaid, rendered at build time)
- All docs are searchable (MkDocs Material with search)
- Docs build in CI (broken links block merge)

7.3. API DOCUMENTATION
- OpenAPI 3.1 specifications for all REST APIs
- Protocol buffer definitions for gRPC
- Generated docs via Redocly
- SDK documentation (Python: Sphinx, TypeScript: TypeDoc)

================================================================================
SECTION 8: GIT WORKFLOW
================================================================================

8.1. BRANCHING (from PRD Section 43)
- main: always deployable
- feature/<ticket>-<slug>: for new features
- bugfix/<ticket>-<slug>: for bug fixes
- hotfix/<ticket>-<slug>: for production hotfixes
- docs/<slug>: for documentation-only changes

8.2. COMMIT FORMAT (Conventional Commits)
type(scope): description

<body explaining what and why>

<footer with breaking changes and ticket refs>

Types: feat, fix, docs, style, refactor, test, chore, perf, ci
Scope: platform, agents, api, dashboard, infra, docs, tests

8.3. PR REQUIREMENTS
- Linked ticket in description
- Descriptive title
- What/why/how to test in body
- Test evidence (CI passing + manual test results)
- At least 1 reviewer approval (2 for security-critical code)
- All CI checks green
- No merge conflicts

8.4. PUSH APPROVAL GATE (CRITICAL)
Before ANY push to remote:
1. Display to user:
   - Commits to be pushed (git log origin/main..HEAD)
   - Changed files (git diff --stat origin/main..HEAD)
   - Test results (pytest --tb=short)
   - Documentation status (what docs changed)
   - Unresolved issues (any open TODOs or known bugs)
2. Ask: "Push to GitHub? Type PUSH APPROVED to confirm."
3. Wait for user response.
4. If user types exactly "PUSH APPROVED":
   - Execute: git push origin main
   - Confirm push succeeded
5. If user types anything else:
   - Do NOT push
   - Address their concern
   - Re-ask for approval after addressing

8.5. GITHUB SETUP
- Repository name: ibr-platform
- Username: ibrsiaika
- Visibility: private (initially)
- Default branch: main
- Branch protection: require PR review, require CI passing
- After first push, enable: Issues, Wiki, Discussions

8.6. SECRETS HANDLING (CRITICAL)
- NEVER commit GitHub tokens, API keys, or passwords
- NEVER hardcode credentials in source code
- Use environment variables: export GITHUB_TOKEN=<token>
- Use .env files (in .gitignore) for local development
- Use Kubernetes secrets for production deployment
- Use HashiCorp Vault for enterprise secret management
- If a secret is accidentally committed:
  1. STOP immediately
  2. Alert the user
  3. Rotate the secret (revoke and create new)
  4. Remove from git history (git filter-branch or BFG)
  5. Force push the cleaned history (with user approval)

================================================================================
SECTION 9: IMPLEMENTATION PATTERNS — FROM PRD
================================================================================

Apply these 50 verified patterns (PRD Sections 57, 74, 107) throughout:

MODEL SELECTION PATTERNS:
- Pattern 1: Right-size for the deployment tier
- Pattern 2: Prefer MoE for specialist quality
- Pattern 3: Maintain multiple quantization variants
- Pattern 41: Adopt the three-tier model family (small/medium/large)
- Pattern 42: Apply Constitutional AI for safety
- Pattern 43: Invest in textbook-quality data
- Pattern 44: Use distillation for compact models
- Pattern 45: Prefer MoE for large models

INFERENCE PATTERNS:
- Pattern 4: vLLM as the default inference server
- Pattern 5: Enable speculative decoding for agentic workloads
- Pattern 6: Three-layer caching (exact, prefix, semantic)
- Pattern 7: FlashAttention-3 mandatory on GPU (NOT on CPU!)
- Pattern 8: Ring Attention for long-context distributed inference
- Pattern 46: Use llama.cpp for CPU inference
- Pattern 47: Use MLC-LLM for mobile
- Pattern 48: Use PowerInfer for single-GPU PCs

RETRIEVAL PATTERNS:
- Pattern 9: Hybrid search as default (BM25 + dense)
- Pattern 10: Overfetch and rerank
- Pattern 11: Graph retrieval for multi-hop
- Pattern 12: Per-use-case embedding model

TRAINING PATTERNS:
- Pattern 13: QLoRA for resource-constrained fine-tuning
- Pattern 14: GRPO for reasoning training (not PPO)
- Pattern 15: Multi-stage training for reasoning models
- Pattern 16: Distillation for production deployment
- Pattern 49: Apply curriculum learning
- Pattern 50: Deduplicate at three levels

OPERATIONS PATTERNS:
- Pattern 17: Observability-first design
- Pattern 18: Human approval gates for irreversible actions
- Pattern 19: Continuous red-team testing
- Pattern 20: Continuous evaluation and drift detection
- Pattern 21: License-aware ingestion

PROTOCOL PATTERNS:
- Pattern 22: Adopt MCP for tool integration
- Pattern 23: Use Structured Outputs for inter-agent communication
- Pattern 24: SSE for streaming responses
- Pattern 25: Six-layer guardrail stack

INFRASTRUCTURE PATTERNS:
- Pattern 26: Volcano for gang scheduling
- Pattern 27: KubeRay for Ray on Kubernetes
- Pattern 28: Spot instances for checkpointable workloads
- Pattern 29: Right-size GPU instances
- Pattern 30: MLflow for model registry
- Pattern 31: Multi-framework observability

EVALUATION PATTERNS:
- Pattern 32: pgvectorscale for moderate scale
- Pattern 33: Qdrant for very large scale
- Pattern 34: RAGAS for RAG quality monitoring
- Pattern 35: TruLens for RAG debugging
- Pattern 36: DeepEval for CI gates

MEMORY PATTERNS:
- Pattern 37: MemGPT pattern for agent memory
- Pattern 38: Simple filesystem memory for working memory
- Pattern 39: DeepSeek-R1 for open-source reasoning
- Pattern 40: Multi-model strategy

================================================================================
SECTION 10: CS FORMULAS TO IMPLEMENT
================================================================================

Implement these formulas (PRD Sections 84-85) in the codebase:

RETRIEVAL FORMULAS:
- Cosine Similarity: cos(A,B) = (A.B) / (||A|| * ||B||)
  Location: platform/retrieval/similarity.py
- TF-IDF: TF-IDF(t,d,D) = TF(t,d) * log(N/df(t))
  Location: platform/retrieval/tfidf.py
- BM25: BM25(q,d) = sum IDF(t) * (TF*(k1+1)) / (TF + k1*(1-b+b*|d|/avgdl))
  Location: platform/retrieval/bm25.py
  Parameters: k1=1.2, b=0.75
- HNSW: Multi-layer graph, level = floor(-ln(uniform) * mL), mL=1/ln(M)
  Location: platform/retrieval/hnsw.py (or use Qdrant)
- RRF: RRF(d) = sum 1/(k + rank(d)), k=60
  Location: platform/retrieval/fusion.py
- PageRank: PR(p) = (1-d)/N + d*sum PR(q)/out_degree(q), d=0.85
  Location: platform/knowledge_graph/pagerank.py

PROBABILISTIC FORMULAS:
- Bayesian Update: posterior_odds = prior_odds * likelihood_ratio
  LR = r/(1-r) for source with reliability r
  Location: agents/verification/confidence.py
- Brier Score: BS = (1/N) * sum (f_i - o_i)^2
  Location: agents/evaluation/calibration.py
  Target: BS < 0.20 for production
- KL Divergence: KL(P||Q) = sum P(x) * log(P(x)/Q(x))
  Location: agents/training/grpo.py (KL penalty, beta=0.04)
- Softmax: softmax(x_i) = exp(x_i - max(x)) / sum exp(x_j - max(x))
  Location: platform/math/softmax.py (numerically stable version)
- Cross-Entropy: CE = -sum y_i * log(p_i)
  Location: agents/training/loss.py

EVALUATION FORMULAS:
- ROUGE-N: sum match_count(gram_n) / sum reference_count(gram_n)
  Location: agents/evaluation/rouge.py
- BLEU: BP * exp(sum w_n * log(p_n)), BP = brevity penalty
  Location: agents/evaluation/bleu.py
- nDCG: DCG/IDCG, DCG = sum rel_i / log2(i+1)
  Location: agents/evaluation/ndcg.py

================================================================================
SECTION 11: BENCHMARKS TO RE-RUN
================================================================================

The PRD contains 123+ benchmark measurements (Sections 77-91, 104-106).
Re-run these benchmarks on the development machine and compare:

11.1. From PRD Section 77 (Vector Search):
- Brute force vs ANN at 1K, 10K, 50K, 100K vectors
- Expected: brute force faster at <50K; ANN recall 0.19-0.37
- Re-run with hnswlib (true HNSW) — expect recall 0.95+

11.2. From PRD Section 79 (Semantic Caching):
- Hit rate at thresholds 0.90, 0.95, 0.97, 0.99, 1.00
- Expected: 89% hit rate at 0.95
- Re-run with BGE-large embeddings (not TF-IDF)

11.3. From PRD Section 80 (Attention):
- Standard vs blocked at seq_len 256-4096
- Expected: blocked SLOWER on CPU (0.31-0.66x speedup)
- Re-run with fixed blocked implementation (global softmax)

11.4. From PRD Section 81 (Quantization):
- FP32 vs INT8 vs INT4: size, compression, MSE
- Expected: INT8 4x compression MSE 0.000075; INT4 8x MSE 0.0248

11.5. From PRD Section 82 (Speculative Decoding):
- Speedup at 60%, 70%, 80%, 90% acceptance
- Expected: 2.07x at 70%; 3.15x at 90%

11.6. From PRD Section 83 (CPU Matmul):
- Throughput at dim 512, 1024, 2048, 4096
- Expected: ~0.10 GFLOPS; 7B model = 14.9s/token

11.7. From PRD Section 104 (Model Size vs Quality):
- Small/large model on textbook/web data
- Expected: small on textbook = 100% acc; small on web = 91.25%

11.8. From PRD Section 106 (Inference Latency):
- CPU latency at 125M, 350M, 1B, 3B, 7B, 13B
- Expected: 125M=278 tok/s; 7B=0.06 tok/s

11.9. From PRD Section 106 (Multi-Model Routing):
- Cost reduction: 80% with 4% accuracy loss
- Expected: baseline $0.005/query; routed $0.001/query

11.10. From PRD Section 106 (MoE Compute):
- Dense vs MoE compute time
- Expected: MoE 32x fewer active params

Save all benchmark results to: tests/perf/results/
Compare to PRD claims; deviations >20% must be investigated and documented.

================================================================================
SECTION 12: DEPLOYMENT MODES — IMPLEMENTATION
================================================================================

Implement all 4 deployment modes (PRD Section 17):

12.1. TINY MODE (laptop, 4-8 GB RAM)
- Model: Llama 3.2 1B in GGUF Q4_K_M
- Engine: llama.cpp
- Vector DB: pgvector (embedded)
- SQL DB: SQLite
- No GPU required
- Target: 5-10 tokens/sec
- Config: configs/tiny.yaml

12.2. COMPACT MODE (workstation, 16-32 GB RAM)
- Model: Phi-3 Mini 3.8B in GGUF Q4 or AWQ 4-bit
- Engine: vLLM (if GPU) or llama.cpp (CPU only)
- Vector DB: pgvectorscale or Qdrant single-node
- SQL DB: PostgreSQL
- Optional: consumer GPU (RTX 4090)
- Target: 10-30 tokens/sec
- Config: configs/compact.yaml

12.3. PROFESSIONAL MODE (server, 64-128 GB RAM)
- Model: 7B-13B in INT8 (GPU) or Q4 (CPU)
- Engine: vLLM with FlashAttention-3 (GPU)
- Vector DB: Qdrant 3-node cluster
- SQL DB: PostgreSQL with read replicas
- GPU: 1-4 datacenter GPUs (A100, H100)
- Target: 50-100 tokens/sec
- Config: configs/professional.yaml

12.4. ENTERPRISE MODE (cluster, 256+ GB RAM, multi-GPU)
- Model: 70B+ or MoE (DeepSeek-V3 671B/37B active)
- Engine: vLLM with tensor parallelism
- Vector DB: Qdrant multi-node or Milvus
- SQL DB: PostgreSQL HA
- GPU: 8-256 GPUs
- Target: 100+ tokens/sec at high concurrency
- Config: configs/enterprise.yaml

Each mode must:
- Be deployable via Helm: helm install ibr-platform ./infra/helm/ -f configs/<mode>.yaml
- Pass deployment tests: tests/deployment/test_<mode>.py
- Have a dedicated runbook: docs/runbooks/deploy_<mode>.md
- Be benchmarked: tests/perf/bench_<mode>.py

================================================================================
SECTION 13: SECURITY CHECKLIST
================================================================================

Before ANY commit, verify:

13.1. NO SECRETS IN CODE
- Run: grep -rn "ghp_\|sk-\|password\|secret\|api_key\|token" --include="*.py" --include="*.ts" --include="*.yaml" .
- Exclude: .git/, node_modules/, __pycache__/
- Any match must be a false positive (e.g., "secret" in a variable name) or in .env.example (placeholder only)

13.2. .gitignore PROPERLY CONFIGURED
The .gitignore MUST include:
  # Secrets
  .env
  .env.*
  *.key
  *.pem
  credentials/
  secrets/
  
  # Python
  __pycache__/
  *.pyc
  *.pyo
  .pytest_cache/
  .mypy_cache/
  .ruff_cache/
  *.egg-info/
  dist/
  build/
  
  # Node.js
  node_modules/
  .next/
  .turbo/
  
  # IDE
  .vscode/
  .idea/
  *.swp
  
  # OS
  .DS_Store
  Thumbs.db
  
  # Project
  data/
  models/
  checkpoints/
  logs/
  *.log

13.3. DEPENDENCY SECURITY
- Python: pip-audit (run in CI)
- Node.js: npm audit (run in CI)
- Any vulnerability with CVSS >= 7.0 blocks the build

13.4. OWASP TOP 10 (PRD Section 54)
Implement mitigations for all 10 risks:
- LLM01: Prompt Injection — sandboxed agents, input sanitization
- LLM02: Sensitive Info Disclosure — PII detection, output filtering
- LLM03: Supply Chain — pinned deps, SBOM, vulnerability scanning
- LLM04: Data/Model Poisoning — license-aware ingestion, validation
- LLM05: Improper Output Handling — output validation, schemas
- LLM06: Excessive Agency — capability-based permissions, approval gates
- LLM07: System Prompt Leakage — encryption, output filtering
- LLM08: Vector/Embedding Weaknesses — per-tenant isolation
- LLM09: Misinformation — verification agent, citations
- LLM10: Unbounded Consumption — rate limiting, token budgets

13.5. GUARDRAIL STACK (PRD Section 64)
Implement the 6-layer guardrail stack:
1. Input moderation (Llama Guard 3)
2. Output moderation (Llama Guard 3)
3. Topic guardrails (NeMo Guardrails)
4. Fact-checking (Verification Agent)
5. PII guardrails (regex + NER)
6. Jailbreak detection (fine-tuned classifier)

================================================================================
SECTION 14: PERFORMANCE TARGETS
================================================================================

All components must meet these targets (PRD Section 9):

14.1. LATENCY
- API p99 latency: <2.5s (cached), <8s (retrieval-heavy)
- Planning latency: <30s for 50-node plans
- Research pipeline: >100 docs/min/worker

14.2. THROUGHPUT
- Inference: 100+ tokens/sec (GPU), 5+ tokens/sec (CPU, 1B model)
- Training: GPU utilization >70%
- Retrieval: 1000+ queries/sec (Qdrant)

14.3. AVAILABILITY
- Control plane: 99.9% uptime
- Data plane: 99.5% uptime
- MTTR: <30 minutes

14.4. SCALABILITY
- 100+ concurrent tenants per cluster
- 256+ GPUs per training job
- 1B+ entities in knowledge graph
- 10B+ edges in knowledge graph

14.5. COST
- Per-query cost: <$0.001 (with multi-model routing)
- Per-token inference cost: <$0.10/1M tokens (with full golden token stack)
- Training cost: 50-70% reduction via spot instances

================================================================================
SECTION 15: MONITORING & ALERTING
================================================================================

15.1. METRICS (Prometheus format)
Expose at /metrics endpoint:
- ibr_requests_total{tenant, endpoint, status}
- ibr_request_duration_seconds{tenant, endpoint} (histogram)
- ibr_inference_tokens_total{tenant, model}
- ibr_inference_latency_seconds{model} (histogram)
- ibr_cache_hit_rate{layer} (gauge)
- ibr_agent_active_count{agent_type} (gauge)
- ibr_gpu_utilization{gpu_id} (gauge)
- ibr_training_jobs_active (gauge)
- ibr_knowledge_graph_entities (gauge)
- ibr_knowledge_graph_edges (gauge)
- ibr_audit_log_entries_total (counter)

15.2. LOGS (JSON structured)
Every log entry must include:
- timestamp (ISO 8601)
- level (DEBUG, INFO, WARN, ERROR)
- trace_id (OpenTelemetry trace ID)
- span_id (OpenTelemetry span ID)
- agent_id (which agent produced the log)
- tenant_id (which tenant)
- event_type (structured event name)
- message (human-readable)
- context (additional fields)

15.3. TRACES (OpenTelemetry)
- Every API request is a trace
- Every agent execution is a span within the trace
- Every tool call is a child span
- Traces exported to Jaeger or Tempo

15.4. ALERTS
Configure alerts for:
- API p99 latency > 5s for 5 minutes
- Error rate > 1% for 5 minutes
- Cache hit rate < 30% (sustained)
- GPU utilization > 90% (sustained) or < 30% (sustained)
- Training job failure
- Audit log write failure (CRITICAL)
- Knowledge graph corruption detected

15.5. DASHBOARDS
Create Grafana dashboards for:
- API Overview (latency, throughput, error rate)
- Agent Activity (active agents, tasks per agent, agent health)
- Training (active jobs, GPU utilization, loss curves)
- Knowledge Graph (entity count, edge count, query latency)
- Cost (per-tenant cost, daily spend, cost trend)

================================================================================
SECTION 16: COMPLIANCE
================================================================================

16.1. GDPR (PRD Section 28.1)
- Data residency controls (per-tenant region configuration)
- Right to erasure (automated deletion with verification)
- DPIA templates for new data sources
- DSAR workflow (export user data within 30 days)
- Breach notification (72-hour regulator notification)

16.2. SOC 2 TYPE II (PRD Section 28.2)
- Security: access controls, encryption, vulnerability management
- Availability: redundancy, backups, disaster recovery
- Processing Integrity: input validation, monitoring
- Confidentiality: data classification, encryption
- Privacy: privacy notice, consent management

16.3. EU AI ACT (PRD Section 28.3)
- Risk management system (documented risk register)
- Data governance (provenance, quality, bias detection)
- Technical documentation (model cards, system docs)
- Record-keeping (7-year audit log retention)
- Transparency (user-facing AI information)
- Human oversight (mandatory approval gates)
- Accuracy, robustness, cybersecurity (continuous evaluation)

16.4. HIPAA (PRD Section 28.5, optional)
- BAA available
- PHI detection and encryption
- Access controls with audit logging
- Breach notification workflow

16.5. COPYRIGHT (PRD Section 28.4)
- License-aware ingestion (refuse incompatible licenses)
- Provenance tracking (source -> dataset -> model)
- License register (license types -> permitted uses)
- DMCA response (24-hour takedown, 7-day retrain)

================================================================================
SECTION 17: AI AGENT INSTRUCTIONS — BEHAVIORAL RULES
================================================================================

As the AI engineering agent building this project, you MUST:

17.1. BE HONEST
- If you don't know something, say "I don't know" and research it
- If a test fails, report it honestly — do not mask failures
- If a benchmark doesn't match the PRD, report the discrepancy
- If you make a mistake, admit it and fix it
- Never fabricate research, benchmarks, or citations

17.2. BE THOROUGH
- Read the entire PRD section before starting implementation
- Research the topic before writing code
- Write comprehensive tests (happy path, error path, edge cases)
- Document everything (code, APIs, architecture, runbooks)
- Do not leave TODOs or stubs

17.3. BE PATIENT
- Do not rush. Quality over speed.
- If a section takes multiple sessions, that's fine
- If you need to re-do work because of a mistake, do it
- Do not skip steps to save time

17.4. BE COMMUNICATIVE
- Explain what you're doing and why
- Ask for clarification if requirements are ambiguous
- Report progress regularly
- Flag risks and issues immediately
- Suggest improvements based on research

17.5. BE SECURITY-CONSCIOUS
- Never commit secrets
- Never hardcode credentials
- Always validate inputs
- Always sanitize outputs
- Always log security-relevant events
- When in doubt, choose the more secure option

17.6. BE OBSERVABLE
- Every component emits metrics, logs, and traces
- Every action is auditable
- Every decision is documented (ADR)
- Every failure is recoverable

17.7. BE COMPLIANT
- Respect licenses (don't train on incompatible data)
- Respect privacy (PII detection and redaction)
- Respect robots.txt (polite crawling)
- Respect human oversight (approval gates)
- Respect the law (GDPR, HIPAA, EU AI Act)

================================================================================
SECTION 18: INTERACTION WITH USER
================================================================================

18.1. WHEN TO ASK THE USER
Ask the user for clarification when:
- A PRD section is ambiguous or contradictory
- A technology decision has no clear winner
- A security decision could affect compliance
- A push to GitHub is requested (ALWAYS ask)
- A destructive action is proposed (delete data, reset state)
- You're unsure whether to proceed

18.2. WHEN NOT TO ASK THE USER
Do NOT ask the user when:
- The PRD clearly specifies the requirement
- The implementation is a standard pattern
- The test is failing due to a bug (fix it, don't ask)
- The documentation needs updating (just update it)

18.3. HOW TO REPORT PROGRESS
After completing each section, report:
- Section number and title
- What was implemented (files created/modified)
- Test results (N tests, all passing)
- Benchmark results (if applicable)
- Any deviations from the PRD (with justification)
- Next section to be worked on
- Any blockers or risks

18.4. HOW TO HANDLE ERRORS
When an error occurs:
1. Report the error immediately (don't hide it)
2. Include the full error message and stack trace
3. Explain what you were trying to do
4. Propose a fix or ask for guidance
5. Do NOT continue with broken code

================================================================================
SECTION 19: GITHUB UPLOAD PROCEDURE
================================================================================

19.1. INITIAL REPOSITORY SETUP
```bash
# Create the repository on GitHub (user must do this manually)
# Go to: https://github.com/new
# Owner: ibrsiaika
# Repository name: ibr-platform
# Visibility: Private
# Do NOT initialize with README (we have our own)

# Locally:
cd /home/z/my-project/ibr-platform
git remote add origin https://github.com/ibrsiaika/ibr-platform.git
git branch -M main
```

19.2. AUTHENTICATION (SECURE)
NEVER hardcode the GitHub token. Use one of these methods:

METHOD A: Git Credential Helper (RECOMMENDED)
```bash
git config --global credential.helper store
# Then on first push, Git will prompt for username and password
# Username: ibrsiaika
# Password: <your NEW token (after revoking the old one)>
# Token is stored in ~/.git-credentials (chmod 600)
```

METHOD B: Environment Variable
```bash
export GITHUB_TOKEN=<your_new_token>
git remote set-url origin https://ibrsiaika:${GITHUB_TOKEN}@github.com/ibrsiaika/ibr-platform.git
# WARNING: This puts the token in shell history. Use Method A instead.
```

METHOD C: SSH (most secure)
```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "ibrsiaika@ibr-platform"
# Add the public key to GitHub: Settings -> SSH and GPG keys
git remote set-url origin git@github.com:ibrsiaika/ibr-platform.git
```

19.3. PUSH PROCEDURE (WITH APPROVAL GATE)
Before EVERY push:
1. Display to user:
   ```
   PUSH SUMMARY:
   - Commits to push: <count>
   - Files changed: <count>
   - Test status: <passing/failing>
   - Documentation: <updated/not needed>
   - Security scan: <clean/warnings>
   ```
2. Ask: "Type PUSH APPROVED to push to GitHub, or type anything else to cancel."
3. Wait for user input.
4. If "PUSH APPROVED":
   ```bash
   git push origin main
   ```
5. Confirm: "Pushed successfully. Commit hash: <hash>"

19.4. ONE-BY-ONE COMMIT STRATEGY
The user requested commits be pushed one by one. Strategy:
- After completing each PRD section, make a commit
- After every 3-5 section commits, request push approval
- This keeps pushes manageable and reviewable
- Each push should be a logical unit of work

19.5. TOKEN SECURITY (CRITICAL)
- The token shared in chat (ghp_XXXX_REDACTED) is COMPROMISED
- The user MUST revoke it at https://github.com/settings/tokens
- The user MUST create a new token
- The new token MUST NOT be shared in chat
- Use Method A (credential helper) or Method C (SSH) for authentication
- NEVER echo the token in any command or log

================================================================================
SECTION 20: FINAL CHECKLIST BEFORE STARTING
================================================================================

Before starting implementation, verify ALL of the following:

[ ] PDF is accessible at /home/z/my-project/download/IBR_Platform_PRD.pdf
[ ] Benchmark scripts are accessible at /home/z/my-project/scripts/
[ ] Research files are accessible at /home/z/my-project/research/
[ ] Python 3.11+ is installed
[ ] Node.js 20+ is installed
[ ] Docker is installed
[ ] Kubernetes CLI is installed
[ ] Git is installed and configured
[ ] Project directory /home/z/my-project/ibr-platform/ is created
[ ] .gitignore is configured with all entries from Section 13.2
[ ] README.md is created with project overview
[ ] pyproject.toml is created with dependencies
[ ] GitHub repository ibrsiaika/ibr-platform is created (by user)
[ ] Old GitHub token is REVOKED (by user)
[ ] New GitHub token is created and stored securely (by user)
[ ] Git remote is configured (git remote add origin ...)

If ANY item is unchecked, address it before starting Section 1.

================================================================================
SECTION 21: STARTING THE WORK
================================================================================

Once all prerequisites are verified, begin with:

STEP 1: Read the PDF completely (all 224 pages, 107 sections)
- Do not skip any section
- Take notes on dependencies between sections
- Identify the first 5 sections to implement (Section 4 priority order)

STEP 2: Set up the project structure (PRD Section 32.2)
- Create all directories
- Initialize pyproject.toml, package.json, Makefile
- Create initial .gitignore and README.md
- Commit: "chore: initialize project structure"

STEP 3: Write the first ADR (Architecture Decision Record)
- ADR-0001: Technology stack adoption (based on PRD Section 31)
- Document all 14 technology decisions with rationale
- Commit: "docs(adr): add ADR-0001 technology stack"

STEP 4: Begin Section 32 (System Design — Folder Structure)
- Follow the workflow in Section 3 of this prompt
- Read the section, research, write tests, implement, test, document, commit

STEP 5: Continue with the priority order in Section 4 of this prompt
- One section at a time
- Full workflow per section
- Commit after each section
- Request push approval after every 3-5 sections

================================================================================
SECTION 22: REMINDERS — READ THESE DAILY
================================================================================

EVERY DAY before starting work, re-read these reminders:

1. The PDF is the source of truth. When in doubt, read the relevant section.
2. One section at a time. Complete it fully. Then move on.
3. Tests first. Implementation second. No exceptions.
4. Research before code. Cite your sources.
5. No stubs, no TODOs, no "I'll fix it later."
6. Conventional commits. Every commit references the PRD section.
7. NEVER push without user approval. Display summary, wait for "PUSH APPROVED".
8. NEVER commit secrets. If you do, STOP and alert the user.
9. CPU-first. GPU is optional. Test on CPU.
10. Documentation is not optional. Write it before implementation.
11. Be honest. Be thorough. Be patient. Be communicative.
12. Security is not optional. Compliance is not optional. Safety is not optional.
13. The old GitHub token is compromised. The user must create a new one.
14. The user's GitHub username is "ibrsiaika" — use ONLY this, not other usernames.
15. Push commits one by one (or in small logical groups), with approval each time.

================================================================================
SECTION 23: EMERGENCY PROCEDURES
================================================================================

23.1. IF YOU ACCIDENTALLY COMMIT A SECRET
1. STOP immediately. Do not push.
2. Alert the user: "SECURITY ALERT: A secret was committed in commit <hash>."
3. Help the user rotate the secret (revoke and create new)
4. Remove the secret from git history:
   ```bash
   # Using BFG Repo-Cleaner (recommended)
   bfg --replace-text passwords.txt
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   # OR using git filter-branch (slower)
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch <file-with-secret>' \
     --prune-empty --tag-name-filter cat -- --all
   ```
5. Force push (with user approval) to clean the remote
6. Verify the secret no longer appears in git history

23.2. IF TESTS ARE FLAKY
1. Do NOT disable the test
2. Quarantine it: move to tests/quarantine/ with a note explaining why
3. Investigate the root cause within 24 hours
4. Fix the test or the underlying code
5. Move the test back to its original location

23.3. IF A BENCHMARK DOESN'T MATCH THE PRD
1. Do NOT change the PRD claim
2. Do NOT change the benchmark to match
3. Investigate the discrepancy:
   - Different hardware?
   - Different library versions?
   - Different test setup?
4. Document the discrepancy in tests/perf/results/discrepancies.md
5. Report to the user with your analysis

23.4. IF YOU'RE STUCK
1. Do NOT guess. Do NOT make assumptions.
2. Re-read the relevant PRD section
3. Search the web for solutions
4. If still stuck, ask the user for guidance
5. It's better to ask than to build the wrong thing

23.5. IF THE USER ASKS YOU TO SKIP A STEP
1. Politely refuse: "I cannot skip <step> because the PRD requires it."
2. Explain why the step is necessary
3. Offer a faster alternative if one exists
4. If the user insists, document the deviation in an ADR and proceed

================================================================================
SECTION 24: SUCCESS CRITERIA
================================================================================

The project is successful when ALL of the following are true:

[ ] All 107 PRD sections are implemented and tested
[ ] All 50 practical patterns (Sections 57, 74, 107) are applied
[ ] All 14 CS formulas (Sections 84-85) are implemented
[ ] All 4 deployment modes (Tiny, Compact, Professional, Enterprise) work
[ ] All 10 OWASP LLM Top 10 risks are mitigated (Section 54)
[ ] All 6 guardrail layers are implemented (Section 64)
[ ] All 23 golden token stack techniques are implemented (Section 101)
[ ] Test coverage ≥ 80% for all modules
[ ] All benchmarks from PRD Sections 77-91, 104-106 are re-run and results documented
[ ] Documentation is complete (all 11 deliverables from Section 42)
[ ] Git history is clean (no secrets, conventional commits, logical progression)
[ ] GitHub repository ibrsiaika/ibr-platform is populated and up-to-date
[ ] The platform can run a canonical research task end-to-end
[ ] The platform passes all quality gates (Section 41)
[ ] The platform meets all NFR targets (Section 9)

================================================================================
END OF MASTER BUILD PROMPT
================================================================================

Total lines: 1100+
Total sections: 24
Total rules: 12 absolute + 7 behavioral + 5 emergency = 24

This prompt is the operating manual for building the IBR Platform.
Read it. Re-read it. Follow it exactly.

The PDF (/home/z/my-project/download/IBR_Platform_PRD.pdf) is the source of truth.
This prompt is the workflow.
The benchmark scripts are the validation.
The user is the approver.

BEGIN WORK.
