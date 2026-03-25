# Contributing

Thank you for your interest in contributing to OpenAICE!

## Getting Started

1. Fork and clone the repository
2. Install development dependencies:

```bash
pip install poetry
poetry install
```

3. Run tests to ensure everything works:

```bash
pytest tests/ -v
```

## Development Workflow

### Making Changes

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Add tests for new functionality
4. Run the test suite: `pytest tests/ -v`
5. Submit a pull request

### Code Style

- We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Type hints are required for all public functions
- Docstrings follow Google style

```bash
ruff check .
ruff format .
```

## What to Contribute

### High-Impact Areas

| Area | Description | Difficulty |
|------|------------|-----------|
| **New adapters** | Integrate additional telemetry/runtime sources | Medium |
| **Policy rules** | Add decision rules for new scenarios | Easy |
| **Replay scenarios** | Create test scenarios for edge cases | Easy |
| **Documentation** | Improve docs, add examples, fix typos | Easy |
| **Core improvements** | State bus, policy engine, guardrails enhancements | Hard |

### Adding a New Adapter

1. Create a new file in `openaice/adapters/telemetry/` or `openaice/adapters/runtime/`
2. Implement the `TelemetryAdapter` or `RuntimeStateAdapter` interface
3. Add tests in `tests/`
4. Document in `docs/adapters/`
5. See the [Writing Custom Adapters](adapters/custom.md) guide

### Adding a Policy Rule

1. Add the rule to `policies/rules.yaml`
2. If the rule needs new logic, add a method in `openaice/core/policy_engine.py`
3. Create a replay scenario in `examples/telemetry-replay/`
4. Add a golden test in `tests/test_replay.py`

## Code of Conduct

We expect all contributors to follow standard open-source community guidelines. Be respectful, constructive, and inclusive.

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
