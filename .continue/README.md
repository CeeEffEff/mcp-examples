# Rule Evaluation Service

This service evaluates the effectiveness of rules in controlling LLM agent behavior.

## Features
- Static rule syntax analysis
- Dynamic rule evaluation
- Compliance scoring
- Report generation

## Usage
```python
from main import run_rule_evaluation

rules = [...]  # List of rules to evaluate
context = {...}  # Evaluation context
results = run_rule_evaluation(rules, context)
```