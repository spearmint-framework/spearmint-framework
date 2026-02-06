# Comparison to Alternatives

How Spearmint compares to other experiment frameworks.

## vs. Hydra

| Feature | Spearmint | Hydra |
|---------|-----------|-------|
| **Use case** | Runtime experiments | CLI configuration |
| **Config injection** | Decorator-based | CLI args |
| **Online experiments** | ✅ Excellent | ❌ Limited |
| **Offline experiments** | ✅ Good | ✅ Excellent |
| **A/B testing** | ✅ Built-in | ⚠️ Manual |
| **Type safety** | ✅ Pydantic | ✅ Structured configs |

**Choose Spearmint for:** Online experiments, A/B testing, runtime config switching

**Choose Hydra for:** CLI tools, batch jobs, complex config hierarchies

## vs. LaunchDarkly

| Feature | Spearmint | LaunchDarkly |
|---------|-----------|--------------|
| **Deployment** | Self-hosted | SaaS |
| **Cost** | Free (open source) | Paid |
| **Configuration** | Code-first | UI-driven |
| **Tracing** | MLflow integration | Built-in analytics |
| **Flexibility** | High (Python code) | Medium (UI limits) |

**Choose Spearmint for:** Full control, code-first approach, ML experiments

**Choose LaunchDarkly for:** Enterprise features, multi-language support, managed service

## vs. Manual Parameter Passing

| Approach | Pros | Cons |
|----------|------|------|
| **Spearmint** | Auto propagation, tracing, multi-variant | Learning curve, dependency |
| **Manual** | Full control, no dependencies | Boilerplate, no tracing, error-prone |

**Choose Spearmint when:**
- Testing multiple configurations
- Need automatic config propagation
- Want built-in tracing and evaluation

**Use manual passing when:**
- Single config only
- Maximum performance critical
- Minimal dependencies required

## Feature Matrix

| Feature | Spearmint | Hydra | LaunchDarkly | Manual |
|---------|-----------|-------|--------------|--------|
| Runtime switching | ✅ | ❌ | ✅ | ⚠️ |
| Type safety | ✅ | ✅ | ⚠️ | ✅ |
| Parallel execution | ✅ | ⚠️ | ❌ | ⚠️ |
| Shadow testing | ✅ | ❌ | ✅ | ❌ |
| MLflow integration | ✅ | ⚠️ | ❌ | ❌ |
| Learning curve | Medium | Medium | Low | Low |

## See Also

- [Architecture](architecture.md)
- [Design Decisions](design-decisions.md)
