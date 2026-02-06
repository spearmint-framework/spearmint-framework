# Spearmint Framework Documentation

An experiment framework for testing multiple configurations of your code in parallel or sequentially.

## Documentation Organization

This documentation follows the [Diátaxis](https://diataxis.fr/) framework for clear, organized technical documentation.

### 🎓 [Tutorials](tutorials/index.md)
**Learning-oriented** lessons that take you through a series of steps to complete a project.

- [Getting Started](tutorials/getting-started.md) - Your first experiment
- [Configuration Basics](tutorials/configuration-basics.md) - Working with configurations
- [Building a FastAPI Experiment](tutorials/fastapi-experiment.md) - Real-world application

### 📖 [How-To Guides](how-to/index.md)
**Problem-oriented** guides that show you how to solve specific tasks.

- [Compare Multiple Configurations](how-to/compare-configurations.md)
- [Use Shadow Testing in Production](how-to/shadow-testing.md)
- [Run Parameter Sweeps](how-to/parameter-sweeps.md)
- [Work with Typed Configurations](how-to/typed-configurations.md)
- [Process Datasets](how-to/process-datasets.md)

### 📚 [Technical Reference](reference/index.md)
**Information-oriented** documentation describing the machinery.

- [API Reference](reference/api.md)
- [Configuration System](reference/configuration.md)
- [Branch Strategies](reference/strategies.md)
- [Integration APIs](reference/integrations.md)

### 💡 [Explanation](explanation/index.md)
**Understanding-oriented** discussion that clarifies and illuminates topics.

- [Experiment Lifecycle](explanation/experiment-lifecycle.md)
- [Configuration System Design](explanation/configuration-design.md)
- [Context Isolation](explanation/context-isolation.md)
- [Async Execution Model](explanation/async-model.md)

## Quick Links

- [GitHub Repository](https://github.com/spearmint-framework/spearmint-framework)
- [PyPI Package](https://pypi.org/project/spearmint-framework/)
- [Cookbook Examples](https://github.com/spearmint-framework/spearmint-framework/tree/main/cookbook)
- [Issue Tracker](https://github.com/spearmint-framework/spearmint-framework/issues)

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
    return f"Using {config['model']}: {prompt}"

result = generate_text("Hello world")
``````
