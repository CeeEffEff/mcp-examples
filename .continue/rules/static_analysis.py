  
import re  

def validate_rule_syntax(rule):  
    '''Validate rule syntax using regex patterns'''  
    if not re.match(r"^If\s+.*?\s+then\s+.*$", rule, re.IGNORECASE):  
        return False, "Invalid syntax: Rule must start with 'If' and end with 'then'"  
    return True, "Valid syntax"  

def analyze_rule_semantics(rule):  
    '''Analyze rule semantics for clarity and scope boundaries'''  
    if re.search(r"\b(?:all|every|any)\b", rule, re.IGNORECASE):  
        return False, "Semantic issue: Overly broad language detected"  
    return True, "Clear semantics"  

def evaluate_rule_effectiveness(rule):  
    '''Evaluate rule effectiveness based on the framework guide'''  
    syntax_valid, syntax_msg = validate_rule_syntax(rule)  
    semantics_valid, semantics_msg = analyze_rule_semantics(rule)  
    if syntax_valid and semantics_valid:  
        return True, "Rule is effective: Passes both syntax and semantic checks"  
    else:  
        return False, f"Rule is ineffective: {syntax_msg} {semantics_msg}"  
