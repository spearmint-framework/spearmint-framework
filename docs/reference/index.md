# Technical Reference

Precise technical descriptions of Spearmint's APIs and components.

## API Documentation

### Core APIs
- **[Spearmint Class](api/spearmint.md)**  
  Main class for experiment management

- **[Experiment Decorator](api/experiment.md)**  
  `@experiment()` decorator reference

- **[Runner APIs](api/runner.md)**  
  `Spearmint.run()` and `Spearmint.arun()` context managers

### Configuration APIs
- **[Config Object](api/config.md)**  
  Dictionary-like configuration interface

- **[DynamicValue](api/dynamic-value.md)**  
  Parameter expansion and value generation

- **[Config Parsing](api/config-parsing.md)**  
  `parse_configs()` and file loading

- **[Config Binding](api/config-binding.md)**  
  Type-safe injection with `Bind` and Pydantic

### Result Types
- **[ExperimentCaseResults](api/results.md)**  
  Result container structure

- **[FunctionResult](api/function-result.md)**  
  Individual execution result

- **[ExperimentCase](api/experiment-case.md)**  
  Configuration mapping per execution

## System Components

- **[Branch Strategies](strategies.md)**  
  Configuration selection and execution patterns

- **[Context Management](context.md)**  
  Context variables and isolation

- **[Registry System](registry.md)**  
  Global experiment function registry

## Integration References

- **[MLflow Integration](integrations/mlflow.md)**  
  Automatic trace logging and data access

- **[OpenTelemetry](integrations/opentelemetry.md)**  
  Span creation and attributes

- **[File Handlers](integrations/handlers.md)**  
  YAML and JSONL processing

## Configuration Reference

- **[Configuration Schema](configuration-schema.md)**  
  Valid configuration structure

- **[Config ID Generation](config-ids.md)**  
  How configuration identifiers are created

- **[YAML Format](yaml-format.md)**  
  YAML configuration file specifications

---

## Navigation

**Learning?** See [Tutorials](../tutorials/index.md)  
**Solving a problem?** Check [How-To Guides](../how-to/index.md)  
**Understanding concepts?** Read [Explanations](../explanation/index.md)
