# Spearmint Framework Documentation

Welcome to the Spearmint framework documentation! Spearmint is an experiment framework for testing multiple configurations of your code in parallel or sequentially.

## Quick Links

- **[Getting Started Tutorial](tutorials/getting-started.md)** - New to Spearmint? Start here
- **[API Reference](reference/api.md)** - Complete API documentation
- **[Cookbook](../cookbook/)** - Practical code examples
- **[Architecture](explanation/architecture.md)** - How Spearmint works internally

## Documentation Overview

This documentation follows the [Diátaxis framework](https://diataxis.fr/) for technical documentation:

### 📚 [Tutorials](tutorials/) 
*Learning-oriented guides to get you started*

- [Getting Started](tutorials/getting-started.md)
- [Your First Experiment](tutorials/your-first-experiment.md)
- [Multi-Config Experiments](tutorials/multi-config-experiments.md)

### 🔧 [How-To Guides](how-to/)
*Practical solutions to common problems*

- [Testing Experiments](how-to/testing-experiments.md)
- [Debugging Configuration Issues](how-to/debugging.md)
- [Production Deployment](how-to/production-deployment.md)
- [Performance Tuning](how-to/performance-tuning.md)

### 📖 [Reference](reference/)
*Technical descriptions of APIs and components*

- [API Reference](reference/api.md)
- [Configuration System](reference/configuration.md)
- [Strategies](reference/strategies.md)
- [Runners & Context Managers](reference/runners.md)

### 💡 [Explanation](explanation/)
*Conceptual guides for understanding Spearmint*

- [Architecture Overview](explanation/architecture.md)
- [Design Decisions](explanation/design-decisions.md)
- [Comparison to Alternatives](explanation/comparison-to-alternatives.md)

## Installation

``````bash
pip install spearmint-framework
``````

## Quick Example

``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[{"model": "gpt-4", "temperature": 0.7}])

@mint.experiment()
def generate_text(prompt: str, config: Config) -> str:
    return f"Using {config['model']} at temp {config['temperature']}: {prompt}"

result = generate_text("Hello world")
``````

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/spearmint-framework/spearmint-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/spearmint-framework/spearmint-framework/discussions)
- **Contributing**: [CONTRIBUTING.md](../CONTRIBUTING.md)

## License

Spearmint is released under the MIT License. See [LICENSE](../LICENSE) for details.
