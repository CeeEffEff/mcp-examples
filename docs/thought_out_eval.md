# Plan to Evaluate Two Gemini Models Pairwise Using Vertex AI

## 1. **Prepare Evaluation Dataset**

- **Dataset Requirements**:
  - Minimum 10 prompt-ground truth pairs (as per [docs](https://cloud.google.com/vertex-ai/docs/training/evaluate-model))
  - Ensure prompts align with the system prompt used for evaluation
  - Example format:

    ```json
    {"prompt": "Summarize quantum physics article", "ground_truth": "Quantum mechanics explores..." }
    ```

## 2. **Register Models in Vertex AI Model Registry**

- **Model A (Source)**:
  - Register using `VertexAIModelRegistry` with parameters:

    ```python
    from vertex_ai import ModelRegistry
    ModelRegistry.register_model("gemini-2.5-flash-lite", description="Baseline model")
    ```

- **Model B (Target)**:
  - Register new model with updated parameters (e.g., `temperature=0.7`, `max_output_tokens=512`)

## 3. **Create Batch Prediction Job**

- **Input Format**:
  - JSONL file with request/response pairs:

    ```json
    {"prompt": "Translate summary to Spanish", "model_id": "gemini-2.5-flash-lite", "reference": "Resumen en español"}
    ```

- **Vertex AI SDK**:

  ```python
  from vertex_ai import BatchPredictionJob
  job = BatchPredictionJob.create(
      model_ids=["gemini-2.5-flash-lite", "gemini-2.5-pro"],
      input_path="gs://your-bucket/prompt_data.jsonl",
      output_path="gs://your-bucket/results/"
  )
  ```

## 4. **Pairwise Evaluation Rubric**

- **Metrics**:
  - Accuracy (compare against ground truth)
  - Fluency (check for grammatical errors)
  - Relevance (ensure response addresses query)
- **Implementation**:

  ```python
  def evaluate_pair(response_a, response_b, reference):
      # Apply rubric criteria from [docs](https://cloud.google.com/vertex-ai/docs/training/evaluate-model)
      score_a = calculate_accuracy(response_a, reference)
      score_b = calculate_accuracy(response_b, reference)
      return {"model_a": score_a, "model_b": score_b}
  ```

## 5. **Analyze Results**

- **Output Format**:

  ```json
  {
    "model_a": {"accuracy": 0.92, "fluency": 0.88},
    "model_b": {"accuracy": 0.95, "fluency": 0.91}
  }
  ```

- **Visualization**:
  Use `matplotlib` to plot metric comparisons:

  ```python
  import matplotlib.pyplot as plt
  plt.bar(["Model A", "Model B"], [0.92, 0.95])
  plt.title("Accuracy Comparison")
  ```

## 6. **Iterate Based on Metrics**

- Use `VertexAIModelRegistry` to update model parameters:

  ```python
  ModelRegistry.update_model("gemini-2.5-pro", temperature=0.6)
  ```

- Repeat evaluation cycle with updated models

---

**References**:

- [Vertex AI Model Evaluation Guide](https://cloud.google.com/vertex-ai/docs/training/evaluate-model)
- [Batch Prediction Format](https://cloud.google.com/vertex-ai/docs/prediction/batch-prediction)
- [Model Registry API](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.models)
