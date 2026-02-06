# Config Parsing

Functions for loading and parsing configuration sources into `Config` objects.

## Overview

Spearmint can load configurations from multiple sources:
- Python dictionaries
- Pydantic models
- YAML files
- YAML directories
- Config objects

The `parse_configs()` function handles all these sources and returns a list of `Config` objects.

## Function: parse_configs

Main function for parsing configuration sources.

### Signature

``````python
def parse_configs(
    configs: Sequence[Any],
    config_handler: Callable[[str | Path], list[dict[str, Any]]]
) -> list[Config]
``````

### Parameters

#### `configs`
**Type:** `Sequence[Any]`

Sequence of configuration sources. Each item can be:
- **dict**: Python dictionary
- **BaseModel**: Pydantic model instance
- **str**: File path to YAML file or directory
- **Path**: pathlib.Path to YAML file or directory
- **Config**: Pre-parsed Config object

#### `config_handler`
**Type:** `Callable[[str | Path], list[dict[str, Any]]]`

Function to handle file/directory paths. Spearmint provides `yaml_handler` for YAML files.

### Returns

**Type:** `list[Config]`

List of parsed and validated Config objects.

### Example

``````python
from spearmint.configuration import parse_configs
from spearmint.utils.handlers import yaml_handler

configs = parse_configs(
    configs=[
        {"model": "gpt-4"},
        "config.yaml",
        Path("configs/")
    ],
    config_handler=yaml_handler
)
# Returns list of Config objects from all sources
``````

## Parsing Dictionary Configs

Dictionaries are parsed directly, with DynamicValue expansion:

``````python
from spearmint.configuration import parse_configs, DynamicValue
from spearmint.utils.handlers import yaml_handler

configs = parse_configs(
    configs=[
        {"model": "gpt-4", "temperature": 0.7}
    ],
    config_handler=yaml_handler
)
# Returns: [Config({"model": "gpt-4", "temperature": 0.7, "config_id": "..."})]
``````

### With DynamicValue

``````python
from spearmint.configuration import parse_configs, DynamicValue
from spearmint.utils.handlers import yaml_handler

configs = parse_configs(
    configs=[
        {
            "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
            "temperature": DynamicValue([0.0, 0.7])
        }
    ],
    config_handler=yaml_handler
)
# Returns 4 Config objects (2 models × 2 temperatures)
``````

## Parsing Pydantic Models

Pydantic models are converted to dictionaries then parsed:

``````python
from pydantic import BaseModel
from spearmint.configuration import parse_configs
from spearmint.utils.handlers import yaml_handler

class ModelConfig(BaseModel):
    model: str
    temperature: float
    max_tokens: int = 1000

model_cfg = ModelConfig(model="gpt-4", temperature=0.7)

configs = parse_configs(
    configs=[model_cfg],
    config_handler=yaml_handler
)
# Returns: [Config({"model": "gpt-4", "temperature": 0.7, "max_tokens": 1000, ...})]
``````

## Parsing YAML Files

### Single File

``````yaml
# config.yaml
model: gpt-4
temperature: 0.7
max_tokens: 1000
``````

``````python
from spearmint.configuration import parse_configs
from spearmint.utils.handlers import yaml_handler

configs = parse_configs(
    configs=["config.yaml"],
    config_handler=yaml_handler
)
# Returns: [Config({"model": "gpt-4", "temperature": 0.7, "max_tokens": 1000, ...})]
``````

### Directory of YAML Files

``````
configs/
├── config1.yaml
├── config2.yaml
└── config3.yaml
``````

``````python
from spearmint.configuration import parse_configs
from spearmint.utils.handlers import yaml_handler

configs = parse_configs(
    configs=["configs/"],
    config_handler=yaml_handler
)
# Returns list of Config objects, one per YAML file
``````

### With Path Objects

``````python
from pathlib import Path
from spearmint.configuration import parse_configs
from spearmint.utils.handlers import yaml_handler

config_path = Path("configs/production.yaml")

configs = parse_configs(
    configs=[config_path],
    config_handler=yaml_handler
)
``````

## Function: generate_configurations

Generates multiple configurations from a single dict with DynamicValues.

### Signature

``````python
def generate_configurations(config: dict[str, Any]) -> list[Config]
``````

### Parameters

#### `config`
**Type:** `dict[str, Any]`

Configuration dictionary that may contain DynamicValue instances.

### Returns

**Type:** `list[Config]`

List of Config objects with all DynamicValue combinations expanded.

### Example

``````python
from spearmint.configuration import generate_configurations, DynamicValue

configs = generate_configurations({
    "model": DynamicValue(["gpt-4", "gpt-3.5-turbo"]),
    "temperature": DynamicValue([0.0, 0.5, 1.0]),
    "max_tokens": 1000
})

# Returns 6 Config objects:
# Config({"model": "gpt-4", "temperature": 0.0, "max_tokens": 1000})
# Config({"model": "gpt-4", "temperature": 0.5, "max_tokens": 1000})
# Config({"model": "gpt-4", "temperature": 1.0, "max_tokens": 1000})
# Config({"model": "gpt-3.5-turbo", "temperature": 0.0, "max_tokens": 1000})
# Config({"model": "gpt-3.5-turbo", "temperature": 0.5, "max_tokens": 1000})
# Config({"model": "gpt-3.5-turbo", "temperature": 1.0, "max_tokens": 1000})
``````

## YAML Handler

The default YAML file handler.

### Function: yaml_handler

``````python
def yaml_handler(path: str | Path) -> list[dict[str, Any]]
``````

Loads YAML file(s) and returns dictionaries.

**Behavior:**
- **File path**: Loads single YAML file
- **Directory path**: Loads all `.yaml` and `.yml` files in directory
- **Invalid path**: Raises FileNotFoundError

### Example: Custom Handler

You can provide a custom config handler:

``````python
from pathlib import Path
from spearmint.configuration import parse_configs

def json_handler(path: str | Path) -> list[dict[str, Any]]:
    """Load JSON configuration files."""
    import json
    
    path = Path(path)
    
    if path.is_file():
        with open(path) as f:
            return [json.load(f)]
    
    if path.is_dir():
        configs = []
        for json_file in path.glob("*.json"):
            with open(json_file) as f:
                configs.append(json.load(f))
        return configs
    
    raise FileNotFoundError(f"Path not found: {path}")

# Use custom handler
configs = parse_configs(
    configs=["configs/"],
    config_handler=json_handler
)
``````

## Complete Examples

### Mixed Sources

``````python
from pathlib import Path
from pydantic import BaseModel
from spearmint.configuration import parse_configs, DynamicValue
from spearmint.utils.handlers import yaml_handler

class ProdConfig(BaseModel):
    model: str = "gpt-4"
    temperature: float = 0.7

configs = parse_configs(
    configs=[
        # Dictionary
        {"model": "gpt-3.5-turbo", "temperature": 0.5},
        
        # Pydantic model
        ProdConfig(),
        
        # YAML file
        "configs/experimental.yaml",
        
        # YAML directory
        Path("configs/variants/"),
        
        # With DynamicValue
        {
            "model": DynamicValue(["gpt-4o", "gpt-4o-mini"]),
            "temperature": 0.9
        }
    ],
    config_handler=yaml_handler
)

# Returns all configs merged into single list
``````

### In Spearmint Class

Spearmint uses `parse_configs` internally:

``````python
from spearmint import Spearmint

# These all use parse_configs under the hood
mint = Spearmint(configs=[
    {"model": "gpt-4"},
    "config.yaml",
    Path("configs/")
])
``````

## See Also

- [Config Object](config.md) - Configuration structure
- [DynamicValue](dynamic-value.md) - Generating multiple configs
- [YAML Format](../yaml-format.md) - YAML configuration format
- [File Handlers](../integrations/handlers.md) - Custom file handlers
