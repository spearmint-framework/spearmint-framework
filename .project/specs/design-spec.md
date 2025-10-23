## Spearmint Framework Design Specification (MVP)

### 1. Overview & Goals
Spearmint is a lightweight Python framework for rapid experimentation across multiple configuration variants of an async function. It focuses on:
- Fast iteration on LLM / data processing experiments
- Minimal ceremony (YAML + Pydantic-driven config expansion)
- Observability via MLflow logging
- Parallel fan-out execution with user-controlled downstream flow
- Extensibility via custom strategy modules

Non-goals for MVP: complex DAG pipelines, advanced optimization algorithms (Bayesian/Evolutionary), multi-process or distributed execution, rich artifact management beyond exception traces.

### 2. Core Abstractions
- Config: A dict-like object produced from YAML or Pydantic expansion.
- Strategy: Defines HOW configs are applied for a run (selection pattern + execution mode + return shape). Strategies decide:
    - Selection: single config vs many.
    - Concurrency mode: immediate vs background vs parallel fan-out.
    - Return type: direct result (single branch) vs container of multiple branches.
- Experiment Decorator (@experiment): Wraps an async function and delegates run orchestration to the chosen Strategy.
- Branch: Holds config, status, timing, output or failure info. Always created for each executed config (including shadow/background ones).
- BranchContainer: Strategy-defined aggregate (list or custom object) for multi-branch strategies.
- Logger Backend: MLflow implementation of a minimal logging interface.

### 3. Execution Model & Concurrency
Execution flow depends on Strategy type:
1. Strategy selects one or more configs from the available pool (RoundRobin: one; Shadow: primary + others; MultiBranch: all).
2. For selected configs:
    - RoundRobin: executes chosen config immediately (await function) – returns the direct result (no container) and still logs a single Branch.
    - Shadow: executes primary config immediately (await); schedules remaining configs in background tasks (asyncio.create_task or thread executor) returning only the primary result while other Branches complete asynchronously.
    - MultiBranch: executes all selected configs concurrently (async tasks) and returns a BranchContainer with all Branches when complete.
3. Each Branch records start/end timestamps, status, exception info.
4. Strategies ensure consistent logging semantics (primary run_id vs separate run_ids per branch for MLflow; MVP: separate run per branch always).
Downstream branching is only automatic for MultiBranch (user receives multiple branch outputs); for RoundRobin/Shadow user code treats the function like a normal async call.

Future: streaming container variant that yields Branches as they finish (especially for large config sets).

### 4. Configuration Management
- YAML base set loaded from directory/direct file(s).
- Pydantic model with custom expansion types can programmatically generate additional variations (e.g., Cartesian product, random draws) producing new Config objects.
- Merging precedence: Programmatic expansions override or extend the base set; each final Config has a stable config_id (hash of normalized content or user-provided field).

### 5. Strategies (MVP)
Available base strategies reflect selection & execution semantics:
- RoundRobinStrategy: Chooses a single config each invocation (e.g., cycling or random choice). Returns the direct function result (Branch available via optional inspection API). Use-case: lightweight A/B over time.
- ShadowStrategy: Chooses a designated "primary" (default) config for foreground execution; concurrently (in background) runs all other configs as shadow evaluations. Returns only the primary result immediately. Shadow Branches log status & exceptions; their outputs can be inspected later (e.g., via strategy.get_shadow_results()).
- MultiBranchStrategy: Executes all configs in parallel fan-out; returns a BranchContainer (ordered list) containing all Branch objects with outputs or failures.

Config Source vs Strategy:
Config generation (YAML list + Pydantic expansion) is separate from selection. Strategies receive a pool (sequence/dict) of configs and apply their policy.

Custom strategies: Users implement Strategy protocol specifying methods:
```python
class Strategy(Protocol):
    async def run(self, func: Callable[..., Awaitable[Any]], configs: Sequence[dict], *args, **kwargs) -> Any: ...
```
RoundRobin & Shadow return a single result; MultiBranch returns BranchContainer. The framework type hints use Union for result shape.


### 6. Logging Integration Layer
Minimal logging interface (LoggerBackend):
```python
class LoggerBackend(Protocol):
    async def start_run(self, config: dict) -> str: ...  # returns run_id
    async def log_status(self, run_id: str, status: str, start_ts: float, end_ts: float, retry_count: int = 0) -> None: ...
    async def log_exception(self, run_id: str, exc_type: str, exc_msg: str, traceback_str: str) -> None: ...
    async def log_params(self, run_id: str, params: dict) -> None: ...
```
MLflow backend implements these using mlflow.start_run(), log_params(), set_tags(), and artifact logging for traceback.

### 7. Metadata Model (MVP)
Per Branch:
- config_id
- config (pydantic model or dict)
- start_ts, end_ts, duration
- status: success | failed | skipped
- output (original return value if success)
- exception_info (type, message, stack) if failed

### 8. Error Handling
Policy: fail-fast per branch but proceed with others. Capture rich exception info and log it. No retries in MVP; design allows injection later.

### 9. Extensibility (MVP)
- Strategy registration API. Users provide class adhering to Strategy protocol.
Roadmap: Pre/post hooks, custom loggers, event bus, artifact serializers, output validators.

### 10. Security & Compliance (Placeholder)
MVP: No sensitive data redaction; caution recommended when logging configs containing secrets. Future: redaction filters, PII scrubbing.

### 11. Performance & Scaling
In-process asyncio concurrency. Guidance: limit simultaneous tasks with optional semaphore (future). CPU-bound code should internally offload to executor by user choice. Future: multi-process and distributed execution.

### 12. CLI & Python API (Outline)
Python:
```python
@experiment(strategy=my_strategy)
async def my_func(input_data: str, config: dict) -> Result:
    ...

branches = await my_func("text")
for b in branches:
    if b.status == "success":
        await downstream(b.output)
```
CLI (future): spearmint run --config-dir=configs/ --func=module:my_func --strategy=pydantic:ModelPath.

### 13. Open Questions / Deferred
- Config ID canonicalization algorithm specifics.
- Async streaming container (yield branches as they complete).
- Structured metrics extraction (only timestamps/status now).
- Cancellation semantics (graceful abort & logging).

### 14. Roadmap Summary
Short-term: metrics dict support, retries, hook system.
Mid-term: grid/random strategies, streaming results, artifact management.
Long-term: DAG orchestration, advanced optimization, distributed execution.

### 15. Acceptance Criteria (MVP)
- Decorator delegates to chosen strategy (RoundRobin, Shadow, MultiBranch).
- RoundRobin returns direct result; Shadow returns primary result while background shadow Branches execute; MultiBranch returns BranchContainer with all branches.
- Concurrent execution implemented for Shadow (background others) and MultiBranch (parallel fan-out).
- MLflow logging for each Branch (separate run per config) including params, status, exception trace.
- Custom strategy registration supported.
- Pure async functions; sync function support via internal wrapper.
- Branch object records metadata defined in Section 7.

### 16. Example Directory Structure (Target)
```
src/spearmint/
  __init__.py
  experiment.py        # decorator & execution
  strategies.py        # Strategy protocol + built-ins
  logging.py           # LoggerBackend + MLflow implementation
  branch.py            # Branch dataclass / container types
  config.py            # YAML loader & Pydantic expansion utilities
  registry.py          # Strategy registration
```

### 17. Risks
- Over-simplified logging may force breaking changes later.
- Strategy-defined container (choice E) could fragment user expectations; mitigation: clear base interface.
- Lack of cancellation might lead to orphaned MLflow runs on abrupt termination.

### 18. Next Steps
1. Implement core dataclasses & protocols.
2. Implement @experiment decorator.
3. Add MLflow backend (optional dependency? guard import).
4. Provide YAML loader + minimal Pydantic expansion utility.
5. Add example usage + initial tests.
