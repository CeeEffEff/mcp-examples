# Rule Evaluation Framework v2.0

## Framework Overview  
This framework evaluates the effectiveness of rules in constraining agent behavior through:  
- **Compliance**: Ensures rules enforce expected behavior (e.g., "never use markdown").  
- **Correctness**: Avoids unintended consequences (e.g., "use bullet points only" vs. "use markdown").  
- **Efficiency**: Reduces ambiguity or errors (e.g., "ask clarifying questions before responding").  
- **Scalability**: Adapts to new scenarios (e.g., rules that generalize across domains).  

## Methodology  
1. **Manual Rule Analysis**:  
   - Parse rule text to identify constraints.  
   - Map rules to evaluation dimensions (e.g., "use bullet points only" → **Correctness**).  

2. **Mock Scenario Design**:  
   - Create safe scenarios that test rule applicability.  
   - Define expected outcomes (e.g., "agent must use bullet points, not markdown").  

3. **Agent Simulation**:  
   - Simulate agent behavior without running the rule.  
   - Compare actual behavior against expected outcomes.  

4. **Metrics**:  
   - **Compliance Rate**: % of scenarios where agent adheres to the rule.  
   - **Efficiency Gain**: Reduction in ambiguity or errors post-rule application.  
   - **Scalability Score**: Rule adaptability to new scenarios (1–5 scale).  

5. **Documentation**:  
   - Save findings in `/Users/conor.fehilly/Documents/repos/mcp-examples/.continue/rules/evals/<rule_eval_name.md>`.  
   - Include metrics, scenario details, and rule analysis.  

## Process  
1. **Rule Selection**: Choose a rule from `/Users/conor.fehilly/Documents/repos/mcp-examples/.continue/rules`.  
2. **Manual Analysis**: Interpret rule text and map to evaluation dimensions.  
3. **Scenario Creation**: Design a mock scenario requiring the rule (e.g., "agent must respond in bullet points").  
4. **Agent Simulation**: Simulate agent behavior without the rule, then with the rule.  
5. **Metric Calculation**: Compute compliance rate, efficiency gain, and scalability score.  
6. **Documentation**: Write findings to `/Users/conor.fehilly/Documents/repos/mcp-examples/.continue/rules/evals/<rule_eval_name.md>`.  

## Example Rule Evaluation  
**Rule**: "Never use markdown in outputs."  
**Scenario**: Agent must respond to a query without markdown.  
**Expected Outcome**: Agent uses plain text or bullet points.  
**Metrics**:  
- Compliance Rate: 95% (agent adheres to rule in 95% of cases).  
- Efficiency Gain: 20% reduction in clarification requests.  
- Scalability Score: 4/5 (rule works across domains but may need refinement for complex tasks).  
