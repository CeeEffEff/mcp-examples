# def evaluate_rule(rule, history=None, compressed_history=""):
#     if not history or not isinstance(history, list):
#         raise ValueError(
#             "The 'history' parameter must be a non-empty list of dictionaries."
#         )

#     historical_compliance_rates = [
#         entry.get("Compliance Rate", "0%") for entry in history
#     ]
#     # Continue with the rest of the function


def evaluate_rule(rule, history=None, compressed_history=""):
    if not history or not isinstance(history, list):
        raise ValueError(
            "The 'history' parameter must be a non-empty list of dictionaries."
        )

    # Define historical_compliance_rates
    historical_compliance_rates = [
        entry.get("Compliance Rate", "0%") for entry in history
    ]

    # Compute average compliance rate
    valid_rates = [
        float(rate.strip("%")) for rate in historical_compliance_rates if rate != "N/A"
    ]
    if not valid_rates:
        avg_compliance = 0.0
    else:
        avg_compliance = sum(valid_rates) / len(valid_rates)

    # Rest of the function logic
    # ...

    return {
        "avg_compliance": avg_compliance,
        "rule": rule,
        "compressed_history": compressed_history,
    }


if __name__ == "__main__":
    result = evaluate_rule(
        {
            "Rule Name": "Example Rule (Version 1.0)",
            "Compliance Rate": "95%",
            "Execution Time": "120ms",
            "Strengths": "High compliance rate, acceptable output quality",
            "Weaknesses": "Limited edge case coverage",
            "Recommendations": "Improve edge case handling",
            "Test Scenarios": "Test 1 (Pass), Test 2 (Fail)",
        },
        history=[
            {"Compliance Rate": "88%", "Compliance Status": "Pass"},
            {"Compliance Rate": "82%", "Compliance Status": "Fail"},
        ],
        compressed_history="Historical compliance fluctuated between 82% and 88%",
    )
    print("Rule Evaluation Results:", result)
