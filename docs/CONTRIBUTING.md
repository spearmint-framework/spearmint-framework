# Contributing to Documentation

Thank you for your interest in improving Spearmint's documentation!

## Documentation Structure

We follow the [Diátaxis](https://diataxis.fr/) framework:

- **Tutorials** (`tutorials/`): Learning-oriented lessons for newcomers
- **How-To Guides** (`how-to/`): Problem-oriented recipes for specific tasks
- **Reference** (`reference/`): Information-oriented technical specifications
- **Explanation** (`explanation/`): Understanding-oriented conceptual discussions

## Writing Guidelines

### General Principles

1. **Be concise and clear** - Developers value their time
2. **Use active voice** - "Run the command" not "The command should be run"
3. **Show, don't just tell** - Include code examples
4. **Progressive disclosure** - Start simple, add complexity gradually
5. **Test all code examples** - Every example must work

### Style Guide

- **Headings:** Use sentence case ("Getting started" not "Getting Started")
- **Code blocks:** Always specify the language (e.g., ` ```python`)
- **Commands:** Show both the command and expected output when helpful
- **Links:** Use descriptive text, not "click here"
- **Inclusive language:** Follow [Google's guidelines](https://developers.google.com/style/inclusive-documentation)

### Code Examples

**Good:**
``````python
from spearmint import Spearmint, Config

mint = Spearmint(configs=[{"model": "gpt-4"}])

@mint.experiment()
def generate(prompt: str, config: Config) -> str:
    return f"Result: {prompt}"

result = generate("Hello")  # "Result: Hello"
``````

**Avoid:**
``````python
# Incomplete example without imports or context
mint = Spearmint(...)
@mint.experiment()
def func(config):
    ...
``````

## Content Types

### Tutorials

**Goal:** Teach by building something complete.

**Structure:**
1. Clear learning objectives
2. Prerequisites listed upfront
3. Step-by-step instructions
4. Validation at each step
5. Summary of what was learned
6. Links to next steps

**Example topics:**
- "Build your first experiment"
- "Create a FastAPI service with shadow testing"
- "Process a dataset with parameter sweeps"

### How-To Guides

**Goal:** Solve a specific problem quickly.

**Structure:**
1. Problem statement
2. Solution (direct to the point)
3. Code example
4. Explanation of key concepts
5. Common variations
6. Related how-tos

**Example topics:**
- "Compare multiple configurations"
- "Handle async functions"
- "Debug failed experiments"

### Reference Documentation

**Goal:** Provide complete technical specifications.

**Structure:**
1. Brief description
2. Signature/syntax
3. Parameters with types
4. Return value
5. Examples
6. Related APIs

**Example topics:**
- API reference for `Spearmint` class
- Configuration schema
- Result object structure

### Explanations

**Goal:** Clarify concepts and design decisions.

**Structure:**
1. Introduction to the topic
2. Context and background
3. Detailed explanation
4. Diagrams when helpful
5. Connections to other concepts
6. Further reading

**Example topics:**
- "How experiment lifecycle works"
- "Understanding context isolation"
- "Why use branch strategies?"

## Building the Docs

### Local Preview

We use [MkDocs](https://www.mkdocs.org/) with the Material theme:

``````bash
# Install dependencies
pip install mkdocs-material

# Serve locally
mkdocs serve

# View at http://localhost:8000
``````

### Building Static Site

``````bash
mkdocs build

# Output in site/
``````

## File Organization

``````
docs/
├── index.md              # Documentation homepage
├── tutorials/
│   ├── index.md          # Tutorial landing page
│   ├── getting-started.md
│   └── ...
├── how-to/
│   ├── index.md
│   ├── compare-configurations.md
│   └── ...
├── reference/
│   ├── index.md
│   ├── api/
│   │   ├── spearmint.md
│   │   └── ...
│   └── integrations/
│       └── ...
└── explanation/
    ├── index.md
    ├── experiment-lifecycle.md
    └── ...
``````

## Submitting Changes

1. **Create a branch:** `git checkout -b docs/your-topic`
2. **Make changes:** Edit or create markdown files
3. **Test locally:** Run `mkdocs serve` and verify
4. **Commit:** Use descriptive commit messages
5. **Open PR:** Include "Docs:" prefix in title

**Commit message examples:**
- `Docs: Add tutorial for FastAPI integration`
- `Docs: Fix typo in config reference`
- `Docs: Update async execution examples`

## Documentation Gaps

Current priorities (as of the initial documentation structure):

### High Priority
- [ ] Complete API reference for all public classes
- [ ] FastAPI tutorial (skeleton exists)
- [ ] Configuration basics tutorial (skeleton exists)
- [ ] MLflow integration guide
- [ ] OpenTelemetry setup guide

### Medium Priority
- [ ] Shadow testing how-to
- [ ] Parameter sweeps how-to
- [ ] Typed configurations how-to
- [ ] Custom strategies guide
- [ ] Troubleshooting guide

### Low Priority
- [ ] Performance optimization guide
- [ ] Advanced async patterns
- [ ] Migration guides (when relevant)
- [ ] Video tutorials
- [ ] Architecture diagrams

## Review Checklist

Before submitting documentation changes:

- [ ] All code examples run without errors
- [ ] Links work (no 404s)
- [ ] Spelling and grammar checked
- [ ] Follows Diátaxis structure
- [ ] Inclusive language used
- [ ] Code blocks have language specified
- [ ] Examples are complete (imports, setup, etc.)
- [ ] Prerequisites are listed
- [ ] Cross-references to related docs included

## Questions?

- **Style questions:** See [Google Developer Documentation Style Guide](https://developers.google.com/style)
- **Structure questions:** See [Diátaxis documentation](https://diataxis.fr/)
- **General questions:** Open a [GitHub Discussion](https://github.com/spearmint-framework/spearmint-framework/discussions)

## Resources

- [Diátaxis Framework](https://diataxis.fr/)
- [Google Developer Style Guide](https://developers.google.com/style)
- [Microsoft Writing Style Guide](https://learn.microsoft.com/en-us/style-guide/welcome/)
- [Write the Docs Community](https://www.writethedocs.org/)
- [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
