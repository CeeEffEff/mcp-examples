import json
from typing import Dict, Any, List

def calculate_compliance_rate(rules: Dict[str, Any], agent_responses: List[str]) -> float:
    """Calculate compliance rate with rules"""
    compliant = 0
    for response in agent_responses:
        for rule_id, rule in rules.items():
            if not rule["violated"](response):
                compliant += 1
    return compliant / len(agent_responses)

def calculate_false_positive_rate(rules: Dict[str, Any], agent_responses: List[str]) -> float:
    """Calculate false positive rate"""
    false_positives = 0
    for response in agent_responses:
        for rule_id, rule in rules.items():
            if rule["violated"](response) and not rule["should_be_violated"](response):
                false_positives += 1
    return false_positives / len(agent_responses)

def calculate_rule_coverage(rules: Dict[str, Any], test_cases: List[str]) -> float:
    """Calculate rule coverage"""
    covered = 0
    for rule_id, rule in rules.items():
        for test_case in test_cases:
            if rule["violated"](test_case):
                covered += 1
                break
    return covered / len(rules)

def calculate_action_consistency(rules: Dict[str, Any], agent_actions: List[Dict[str, Any]]) -> float:
    """Calculate how consistently rules are applied across actions"""
    consistent = 0
    for action in agent_actions:
        for rule_id, rule in rules.items():
            if rule["violated"](action["response"]) != rule["should_be_violated"](action["response"]):
                consistent += 1
                break
    return consistent / len(agent_actions)
