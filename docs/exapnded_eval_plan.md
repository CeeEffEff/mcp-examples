# Task for pairwise Question and Answer model evaluation

Refined task structure with implementation details.

## 1. Dataset Preparation (Task #1)

- Subtasks:
  - Create 10+ prompt-ground truth pairs (format: JSON with "prompt" and "ground_truth" fields)
  - Validate dataset alignment with system prompt requirements
  - Store dataset in Google Cloud Storage (gs://bucket/prompt_data.jsonl)
  - Add data quality checks for prompt diversity and ground truth accuracy

## 2. Model Registration (Task #2)

- Subtasks:
  - Register source model ("gemini-2.5-flash-lite") with Vertex AI Model Registry
    - Set description: "Baseline model for comparison"
    - Configure default parameters: temperature=0.7, max_output_tokens=512
  - Register target model ("gemini-2.5-pro") with updated parameters
    - Set description: "Experimental model with enhanced reasoning"
    - Configure parameters: temperature=0.6, max_output_tokens=1024
  - Verify model registration status via Vertex AI console

## 3. Batch Prediction Setup (Task #3)

- Subtasks:
  - Format input JSONL file with request/response structure

    ```json
    {"prompt": "Translate summary to Spanish", "model_id": "gemini-2.5-flash-lite", "reference": "Resumen en español"}
    ```

  - Create Vertex AI BatchPredictionJob configuration
    - Specify model IDs: ["gemini-2.5-flash-lite", "gemini-2.5-pro"]
    - Set input path: gs://your-bucket/prompt_data.jsonl
    - Configure output path: gs://your-bucket/results/
    - Enable parallel processing for 100+ concurrent requests
  - Monitor job status and handle errors (e.g., token limits, format issues)

## 4. Evaluation Implementation (New Task #4)

- Subtasks:
  - Develop pairwise evaluation rubric with:
    - Accuracy scoring (exact match ratio)
    - Fluency check (grammatical error count)
    - Relevance score (query alignment metric)
  - Implement comparison function:

    ```python
    def compare_models(responses, reference):
        scores = {}
        for model, response in responses.items():
            scores[model] = {
                "accuracy": calculate_exact_match(response, reference),
                "fluency": check_grammatical_errors(response),
                "relevance": measure_query_alignment(response, reference)
            }
        return scores
    ```

  - Store results in structured format:

    ```json
    {
      "model_a": {"accuracy": 0.92, "fluency": 0.88},
      "model_b": {"accuracy": 0.95, "fluency": 0.91}
    }
    ```

## 5. Result Analysis (New Task #5)

- Subtasks:
  - Generate visualization reports:
    - Bar charts for accuracy comparison
    - Heatmaps for metric correlations
    - Trend analysis across different prompt types
  - Create dashboard with:
    - Interactive metric filters
    - Model performance timelines
    - Error pattern analysis
  - Export analysis to Google Cloud Storage for review

## 6. Model Iteration (New Task #6)

- Subtasks:
  - Update model parameters based on metrics:

    ```python
    ModelRegistry.update_model("gemini-2.5-pro", temperature=0.5, max_output_tokens=2048)
    ```

  - Re-run evaluation cycle with updated models
  - Track parameter changes and performance metrics in version-controlled documentation

## Summary

This structure provides:

1. Clear implementation steps for each phase
2. Technical specifics for code implementation
3. Quality control checkpoints
4. Visualization and analysis requirements
5. Iterative improvement framework

## Error resolution

The errors indicate that the task management system requires specific **tags** to exist before tasks/subtasks can be created. Let's first create the required tags, then re-attempt task creation.

---

### 🛠️ Step 1: Create Required Tags

Run these commands to create the missing tags:

```bash
taskmaster-ai_add_tag dataset
taskmaster-ai_add_tag model-registration
taskmaster-ai_add_tag batch-prediction
taskmaster-ai_add_tag evaluation-implementation
taskmaster-ai_add_tag result-analysis
taskmaster-ai_add_tag model-iteration
```

---

### 🚀 Step 2: Create Tasks with Tags

Now create the main tasks with the tags:

```bash
taskmaster-ai_add_task "Dataset Preparation" "dataset"
taskmaster-ai_add_task "Model Registration" "model-registration"
taskmaster-ai_add_task "Batch Prediction Setup" "batch-prediction"
taskmaster-ai_add_task "Evaluation Implementation" "evaluation-implementation"
taskmaster-ai_add_task "Result Analysis" "result-analysis"
taskmaster-ai_add_task "Model Iteration" "model-iteration"
```

---

### 📌 Step 3: Add Subtasks

Once tasks are created, add subtasks:

```bash
taskmaster-ai_add_subtask 1 "Create 10+ prompt-ground truth pairs (JSON format)"
taskmaster-ai_add_subtask 1 "Validate dataset alignment with system prompt requirements"
taskmaster-ai_add_subtask 1 "Store dataset in Google Cloud Storage (gs://bucket/prompt_data.jsonl)"
taskmaster-ai_add_subtask 1 "Add data quality checks for prompt diversity and ground truth accuracy"

taskmaster-ai_add_subtask 2 "Register source model (gemini-2.5-flash-lite) with Vertex AI Model Registry"
taskmaster-ai_add_subtask 2 "Register target model (gemini-2.5-pro) with updated parameters"
taskmaster-ai_add_subtask 2 "Verify model registration status via Vertex AI console"

taskmaster-ai_add_subtask 3 "Format input JSONL file with request/response structure"
taskmaster-ai_add_subtask 3 "Create Vertex AI BatchPredictionJob configuration"
taskmaster-ai_add_subtask 3 "Monitor job status and handle errors (token limits, format issues)"

taskmaster-ai_add_subtask 4 "Develop pairwise evaluation rubric (accuracy, fluency, relevance)"
taskmaster-ai_add_subtask 4 "Implement comparison function for model responses"
taskmaster-ai_add_subtask 4 "Store results in structured JSON format"

taskmaster-ai_add_subtask 5 "Generate visualization reports (bar charts, heatmaps, trend analysis)"
taskmaster-ai_add_subtask 5 "Create dashboard with interactive metric filters"
taskmaster-ai_add_subtask 5 "Export analysis to Google Cloud Storage"

taskmaster-ai_add_subtask 6 "Update model parameters based on metrics"
taskmaster-ai_add_subtask 6 "Re-run evaluation cycle with updated models"
taskmaster-ai_add_subtask 6 "Track parameter changes and performance metrics in documentation"
```

---

### ✅ Result

This will create a fully structured task hierarchy with proper tags. Let me know if you'd like to add dependencies between tasks or set priorities!
