  
import time  
import random  

def generate_test_scenarios(rule):  
    """Generate controlled test cases for rule evaluation"""  
    scenarios = [  
        {"input": "If it is raining, then the ground is wet", "expected": True},  
        {"input": "If it is snowing, then the ground is wet", "expected": False},  
        {"input": "If all students pass, then the class passes", "expected": False},  
        {"input": "If any student fails, then the class fails", "expected": True}  
    ]  
    return scenarios  

def evaluate_rule_behavior(rule):  
    """Evaluate rule behavior under different scenarios"""  
    scenarios = generate_test_scenarios(rule)  
    results = []  
    for scenario in scenarios:  
        start_time = time.time()  
        # Simulate rule application  
        if re.search(r"(?:all|every|any)", rule, re.IGNORECASE):  
            result = False  
        else:  
            result = True  
        execution_time = time.time() - start_time  
        results.append({  
            "scenario": scenario,  
            "result": result,  
            "execution_time": execution_time  
        })  
    return results  
