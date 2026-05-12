## 1. Updated facts survey
### 1.1. Facts given in the task
- The project requires implementing a Python service to evaluate LLM rule adherence
- The framework guide is located at `/Users/conor.fehilly/Documents/repos/mcp-examples/.continue/rules/docs/rule_evaluation_framework_v3.md`
- Taskmaster-ai tools are available for project planning via `TaskmasterAiToolAgent`
- Taskmaster dir is `/Users/conor.fehilly/Documents/repos/mcp-examples/.taskmaster`
- **Do not** overwrite `/Users/conor.fehilly/Documents/repos/mcp-examples/.taskmaster/config.json`

### 1.2. Facts that we have learned
- The rule evaluation framework document defines a structured approach to rule adherence evaluation
- The project will require integration with LLMs for evaluation
- Taskmaster-ai, via  `TaskmasterAiToolAgent`, can be used to generate project structure, tasks, and dependencies

### 1.3. Facts still to look up
- Specific requirements of the rule evaluation framework (e.g., rule types, scoring mechanisms)
- Whether the framework requires specific APIs or libraries for LLM interaction
- Existing implementation examples or code structure recommendations from the framework

### 1.4. Facts still to derive
- Mapping between framework requirements and technical implementation
- Required dependencies for the Python service
- Testing and validation strategies for rule evaluation

## 2. Plan
### 2.1. Read the rule evaluation framework document to extract key requirements and evaluation criteria
### 2.2. Use Taskmaster-ai to initialize a new project structure with appropriate configuration ONLY if it doesn't exits yet
### 2.3. Parse the framework document as a PRD to automatically generate initial tasks converting it first yourself if needed
### 2.4. Expand high-level tasks into detailed implementation subtasks
### 2.5. Define required dependencies for LLM integration and rule evaluation
### 2.6. Implement core rule evaluation logic based on framework specifications
### 2.7. Develop testing and validation components for rule adherence checks
### 2.8. Generate task files and organize project structure
### 2.9. Validate project dependencies and task relationships
### 2.10. Prepare for development iteration based on task prioritization
