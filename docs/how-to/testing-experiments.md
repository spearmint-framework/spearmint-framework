# Testing Experiments

Learn how to test code that uses Spearmint experiments.

## Overview

Testing experiment-decorated functions requires understanding how Spearmint injects configurations. This guide covers common testing patterns.

---

## Basic Testing Pattern

### Test a Single Configuration

``````python
import pytest
from spearmint import Spearmint, Config

def test_simple_experiment():
    """Test experiment with single config."""
    # Setup
    configs = [{"multiplier": 2}]
    mint = Spearmint(configs=configs)
    
    @mint.experiment()
    def multiply(x: int, config: Config) -> int:
        return x * config['multiplier']
    
    # Execute
    result = multiply(5)
    
    # Assert
    assert result == 10
``````

### Test Multiple Configurations

``````python
def test_multiple_configs():
    """Test experiment with multiple configs."""
    configs = [
        {"multiplier": 2},
        {"multiplier": 3},
        {"multiplier": 4},
    ]
    mint = Spearmint(configs=configs)
    
    @mint.experiment()
    def multiply(x: int, config: Config) -> int:
        return x * config['multiplier']
    
    # Test each config
    for i, expected in enumerate([10, 15, 20]):
        mint.configs = [configs[i]]  # Select specific config
        result = multiply(5)
        assert result == expected
``````

---

## Using Context Managers

### Test with Sync Runner

``````python
def test_with_runner():
    """Test using context manager."""
    configs = [{"value": 42}]
    mint = Spearmint(configs=configs)
    
    @mint.experiment()
    def get_value(config: Config) -> int:
        return config['value']
    
    with Spearmint.run(get_value) as runner:
        result = runner()
        assert result.main_result.result == 42
``````

### Test with Async Runner

``````python
import pytest

@pytest.mark.asyncio
async def test_async_experiment():
    """Test async experiment."""
    configs = [{"delay": 0.01}]
    mint = Spearmint(configs=configs)
    
    @mint.experiment()
    async def async_task(x: int, config: Config) -> int:
        await asyncio.sleep(config['delay'])
        return x * 2
    
    async with Spearmint.arun(async_task) as runner:
        result = await runner(5)
        assert result.main_result.result == 10
``````

---

## Testing with Type-Safe Configs

### Pydantic Model Binding

``````python
from pydantic import BaseModel
from typing import Annotated
from spearmint.config import Bind

def test_typed_config():
    """Test with Pydantic model binding."""
    class ModelConfig(BaseModel):
        model: str
        temperature: float
    
    configs = [{"model": "gpt-4", "temperature": 0.7}]
    mint = Spearmint(configs=configs)
    
    @mint.experiment()
    def generate(
        prompt: str,
        config: Annotated[ModelConfig, Bind("")]
    ) -> str:
        return f"{config.model}: {prompt}"
    
    result = generate("test")
    assert result == "gpt-4: test"
``````

---

## Testing Strategies

### Test MultiBranch Strategy

``````python
from spearmint.strategies import MultiBranchStrategy

def test_multibranch():
    """Test all configs execute in MultiBranchStrategy."""
    configs = [
        {"id": 1},
        {"id": 2},
        {"id": 3},
    ]
    mint = Spearmint(strategy=MultiBranchStrategy, configs=configs)
    
    @mint.experiment()
    def get_id(config: Config) -> int:
        return config['id']
    
    with Spearmint.run(get_id, await_variants=True) as runner:
        results = runner()
        
        # Get all results
        all_results = [results.main_result.result]
        all_results.extend([v.result for v in results.variant_results])
        
        assert sorted(all_results) == [1, 2, 3]
``````

### Test Shadow Strategy

``````python
from spearmint.strategies import ShadowStrategy

def test_shadow_strategy():
    """Test main config executes, variants in background."""
    configs = [
        {"name": "main"},
        {"name": "variant1"},
        {"name": "variant2"},
    ]
    mint = Spearmint(strategy=ShadowStrategy, configs=configs)
    
    @mint.experiment()
    def get_name(config: Config) -> str:
        return config['name']
    
    result = get_name()
    
    # Only main result returned immediately
    assert result == "main"
    
    # Variants run in background (not awaited by default)
``````

---

## Mocking and Fixtures

### Pytest Fixtures

``````python
import pytest
from spearmint import Spearmint

@pytest.fixture
def mint_instance():
    """Fixture for Spearmint instance."""
    configs = [{"api_key": "test-key", "model": "gpt-4"}]
    return Spearmint(configs=configs)

def test_with_fixture(mint_instance):
    """Test using fixture."""
    @mint_instance.experiment()
    def call_api(prompt: str, config: Config) -> str:
        return f"{config['model']}: {prompt}"
    
    result = call_api("test")
    assert "gpt-4" in result
``````

### Mocking External APIs

``````python
from unittest.mock import patch, MagicMock

def test_with_mock():
    """Test with mocked external API."""
    configs = [{"model": "gpt-4"}]
    mint = Spearmint(configs=configs)
    
    @mint.experiment()
    def call_llm(prompt: str, config: Config) -> str:
        # This would normally call OpenAI
        import openai
        response = openai.chat.completions.create(
            model=config['model'],
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    with patch('openai.chat.completions.create') as mock_api:
        mock_api.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Mocked response"))]
        )
        
        result = call_llm("test prompt")
        
        assert result == "Mocked response"
        mock_api.assert_called_once()
``````

---

## Testing Configuration Loading

### Test YAML Loading

``````python
import tempfile
from pathlib import Path

def test_yaml_config_loading():
    """Test loading config from YAML file."""
    # Create temporary YAML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("model: gpt-4\ntemperature: 0.7")
        config_file = f.name
    
    try:
        mint = Spearmint(configs=[config_file])
        
        @mint.experiment()
        def get_model(config: Config) -> str:
            return config['model']
        
        result = get_model()
        assert result == "gpt-4"
    finally:
        Path(config_file).unlink()  # Clean up
``````

### Test Dynamic Value Expansion

``````python
from spearmint.config import DynamicValue
from spearmint.configuration import generate_configurations

def test_dynamic_value_expansion():
    """Test DynamicValue creates correct configs."""
    config = {
        "model": DynamicValue(["gpt-4", "gpt-3.5"]),
        "temperature": DynamicValue([0.0, 0.5])
    }
    
    expanded = generate_configurations(config)
    
    assert len(expanded) == 4
    assert {"model": "gpt-4", "temperature": 0.0} in expanded
    assert {"model": "gpt-4", "temperature": 0.5} in expanded
    assert {"model": "gpt-3.5", "temperature": 0.0} in expanded
    assert {"model": "gpt-3.5", "temperature": 0.5} in expanded
``````

---

## Testing Error Handling

### Test Missing Config Keys

``````python
def test_missing_config_key():
    """Test behavior with missing config key."""
    configs = [{"model": "gpt-4"}]  # Missing 'temperature'
    mint = Spearmint(configs=configs)
    
    @mint.experiment()
    def use_temperature(config: Config) -> float:
        return config.get('temperature', 0.5)  # Use default
    
    result = use_temperature()
    assert result == 0.5
``````

### Test Invalid Config Values

``````python
def test_invalid_config_validation():
    """Test Pydantic validation catches invalid values."""
    from pydantic import BaseModel, Field
    
    class ValidatedConfig(BaseModel):
        temperature: float = Field(ge=0.0, le=2.0)
    
    configs = [{"temperature": 3.0}]  # Invalid: > 2.0
    mint = Spearmint(configs=configs)
    
    with pytest.raises(Exception):  # Pydantic ValidationError
        @mint.experiment()
        def use_config(config: Annotated[ValidatedConfig, Bind("")]) -> float:
            return config.temperature
        
        use_config()
``````

---

## Integration Testing

### Test Full Pipeline

``````python
def test_full_experiment_pipeline():
    """Integration test for complete experiment flow."""
    configs = [
        {"preprocessor": "lowercase", "model": "simple"},
        {"preprocessor": "uppercase", "model": "simple"},
    ]
    mint = Spearmint(configs=configs)
    
    @mint.experiment()
    def preprocess(text: str, config: Config) -> str:
        if config['preprocessor'] == "lowercase":
            return text.lower()
        return text.upper()
    
    @mint.experiment()
    def process(text: str, config: Config) -> str:
        preprocessed = preprocess(text, config)
        return f"[{config['model']}] {preprocessed}"
    
    result = process("Hello World")
    
    assert result == "[simple] hello world"
``````

---

## Performance Testing

### Test Execution Time

``````python
import time

def test_parallel_execution_speed():
    """Test that parallel execution is faster."""
    configs = [{"id": i} for i in range(10)]
    mint = Spearmint(strategy=MultiBranchStrategy, configs=configs)
    
    @mint.experiment()
    def slow_task(config: Config) -> int:
        time.sleep(0.1)
        return config['id']
    
    start = time.time()
    with Spearmint.run(slow_task, await_variants=True) as runner:
        results = runner()
    duration = time.time() - start
    
    # Should be < 1 second (parallel) vs 1+ seconds (sequential)
    assert duration < 0.5, f"Took {duration}s, expected < 0.5s"
``````

---

## Best Practices

### 1. Use Fixtures for Common Setups

``````python
@pytest.fixture
def default_mint():
    return Spearmint(configs=[{"model": "gpt-4"}])

def test_a(default_mint):
    pass

def test_b(default_mint):
    pass
``````

### 2. Test Edge Cases

``````python
def test_empty_configs():
    """Test behavior with no configs."""
    mint = Spearmint(configs=[])
    # Assert expected behavior
``````

### 3. Isolate Tests

Each test should:
- Create its own Spearmint instance
- Use separate configs
- Not depend on other tests

### 4. Use Descriptive Test Names

``````python
# ✅ Good
def test_experiment_returns_correct_value_with_multiplier_config():
    pass

# ❌ Bad
def test_experiment():
    pass
``````

---

## See Also

- [API Reference](../reference/api.md) - Complete API documentation
- [Configuration System](../reference/configuration.md) - Config management
- [Architecture](../explanation/architecture.md) - How Spearmint works
