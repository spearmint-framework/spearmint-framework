# Explanation

Deep dives into Spearmint's design, concepts, and architecture.

## Core Concepts

- **[Experiment Lifecycle](experiment-lifecycle.md)**  
  What happens when you call an experiment function

- **[Configuration System Design](configuration-design.md)**  
  How configuration parsing, expansion, and injection work

- **[Branch Strategies Explained](branch-strategies.md)**  
  Different execution patterns and when to use them

## Architecture

- **[Context Isolation](context-isolation.md)**  
  How Spearmint maintains separate state across threads and async tasks

- **[Async Execution Model](async-model.md)**  
  Event loops, context propagation, and async support

- **[Registry Pattern](registry-pattern.md)**  
  Global tracking of experiment functions

## Design Decisions

- **[Why Decorators?](why-decorators.md)**  
  The decorator-based API design rationale

- **[Configuration Injection](configuration-injection.md)**  
  Type-safe parameter injection vs manual passing

- **[Variant Execution](variant-execution.md)**  
  Primary vs variant configs and execution modes

## Integration Design

- **[MLflow Integration](mlflow-integration.md)**  
  Automatic trace logging architecture

- **[OpenTelemetry Support](opentelemetry-support.md)**  
  Span creation and attribute conventions

## Advanced Topics

- **[Nested Experiments](nested-experiments.md)**  
  How inner function calls are discovered and executed

- **[Thread Safety](thread-safety.md)**  
  Concurrent execution and isolation guarantees

- **[Performance Considerations](performance.md)**  
  Overhead, optimization, and when not to use Spearmint

---

## Navigation

**New to Spearmint?** Start with [Tutorials](../tutorials/index.md)  
**Need to solve a problem?** Check [How-To Guides](../how-to/index.md)  
**Looking for specifics?** See [Technical Reference](../reference/index.md)
