# Performance Tuning

Optimize Spearmint experiments for better performance.

## Execution Optimization

### Choose Right Strategy

``````python
# ✅ Fast: Single config, no overhead
mint = Spearmint(configs=[config])

# ⚡ Medium: Parallel variants
mint = Spearmint(strategy=MultiBranchStrategy, configs=configs)

# 🐌 Slower: Sequential testing
for config in configs:
    mint = Spearmint(configs=[config])
    result = experiment()
``````

### Async for I/O-Bound Tasks

``````python
@mint.experiment()
async def fetch_data(url: str, config: Config) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
``````

## Memory Management

### Limit Concurrent Variants

``````python
# Avoid too many parallel configs
configs = configs[:5]  # Limit to 5 configs

mint = Spearmint(strategy=MultiBranchStrategy, configs=configs)
``````

### Clean Up Resources

``````python
@mint.experiment()
def process(data: str, config: Config) -> str:
    try:
        result = expensive_operation(data, config)
        return result
    finally:
        cleanup_resources()  # Always cleanup
``````

## Configuration Loading

### Lazy Loading

Load configs on demand:
``````python
def get_configs():
    """Load configs only when needed."""
    return parse_configs(["configs/"])

mint = Spearmint(configs=get_configs())
``````

## See Also

- [Architecture](../explanation/architecture.md)
- [Strategies](../reference/strategies.md)
