"""Quick test to verify config.py implementation."""

from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import BaseModel

from spearmint.config import (
    expand_configs_from_model,
    generate_config_id,
    load_configs_from_yaml,
    merge_configs,
    normalize_config,
)


def test_generate_config_id():
    """Test config ID generation."""
    # Test with explicit config_id
    config1 = {"config_id": "my_id", "param": 1}
    assert generate_config_id(config1) == "my_id"

    # Test hash generation
    config2 = {"param": 1, "name": "test"}
    config3 = {"name": "test", "param": 1}  # Same content, different order
    assert generate_config_id(config2) == generate_config_id(config3)
    assert len(generate_config_id(config2)) == 16

    print("✓ Config ID generation works")


def test_load_yaml_file():
    """Test loading YAML from file."""
    with TemporaryDirectory() as tmpdir:
        yaml_file = Path(tmpdir) / "config.yaml"
        yaml_file.write_text("""
model: gpt-4
temperature: 0.7
max_tokens: 100
""")

        configs = load_configs_from_yaml(yaml_file)
        assert len(configs) == 1
        assert configs[0]["model"] == "gpt-4"
        assert configs[0]["temperature"] == 0.7

    print("✓ YAML file loading works")


def test_load_yaml_list():
    """Test loading list of configs from YAML."""
    with TemporaryDirectory() as tmpdir:
        yaml_file = Path(tmpdir) / "configs.yaml"
        yaml_file.write_text("""
- model: gpt-4
  temperature: 0.7
- model: gpt-3.5-turbo
  temperature: 0.9
""")

        configs = load_configs_from_yaml(yaml_file)
        assert len(configs) == 2
        assert configs[0]["model"] == "gpt-4"
        assert configs[1]["model"] == "gpt-3.5-turbo"

    print("✓ YAML list loading works")


def test_load_yaml_directory():
    """Test loading all YAML files from directory."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create multiple YAML files
        (tmppath / "config1.yaml").write_text("model: gpt-4")
        (tmppath / "config2.yml").write_text("model: claude")
        (tmppath / "readme.txt").write_text("not yaml")

        configs = load_configs_from_yaml(tmppath)
        assert len(configs) == 2  # Only .yaml and .yml files

    print("✓ YAML directory loading works")


def test_expand_from_pydantic():
    """Test config expansion from Pydantic model."""

    class LLMConfig(BaseModel):
        model: str
        temperature: float

    model = LLMConfig(model="gpt-4", temperature=0.7)
    configs = expand_configs_from_model(model)

    assert len(configs) == 1
    assert configs[0]["model"] == "gpt-4"
    assert configs[0]["temperature"] == 0.7
    assert "config_id" in configs[0]

    print("✓ Pydantic expansion works")


def test_expand_with_base_configs():
    """Test merging Pydantic model with base configs."""

    class Override(BaseModel):
        temperature: float

    base_configs = [
        {"model": "gpt-4", "temperature": 0.5},
        {"model": "claude", "temperature": 0.5},
    ]

    override = Override(temperature=0.9)
    expanded = expand_configs_from_model(override, base_configs)

    assert len(expanded) == 2
    assert all(c["temperature"] == 0.9 for c in expanded)
    assert expanded[0]["model"] == "gpt-4"
    assert expanded[1]["model"] == "claude"

    print("✓ Config expansion with base works")


def test_normalize_config():
    """Test config normalization."""
    # Test dict
    config_dict = {"param": 1}
    normalized = normalize_config(config_dict)
    assert "config_id" in normalized

    # Test Pydantic model
    class TestModel(BaseModel):
        param: int

    model = TestModel(param=1)
    normalized = normalize_config(model)
    assert normalized["param"] == 1
    assert "config_id" in normalized

    print("✓ Config normalization works")


def test_merge_configs():
    """Test config merging strategies."""
    base = [{"config_id": "a", "x": 1}, {"config_id": "b", "x": 2}]
    override = [{"config_id": "c", "x": 3}]

    # Test extend
    extended = merge_configs(base, override, strategy="extend")
    assert len(extended) == 3

    # Test override
    override_same = [{"config_id": "a", "x": 999}]
    merged = merge_configs(base, override_same, strategy="override")
    assert len(merged) == 2
    assert merged[0]["x"] == 999 or merged[1]["x"] == 999

    print("✓ Config merging works")


if __name__ == "__main__":
    test_generate_config_id()
    test_load_yaml_file()
    test_load_yaml_list()
    test_load_yaml_directory()
    test_expand_from_pydantic()
    test_expand_with_base_configs()
    test_normalize_config()
    test_merge_configs()
    print("\n✅ All config.py tests passed!")
