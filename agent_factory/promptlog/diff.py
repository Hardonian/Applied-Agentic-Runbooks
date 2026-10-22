"""
Compare runs and generate diffs.
"""

from typing import Any

from agent_factory.promptlog.storage import PromptLogStorage


def diff_runs(
    run_id_1: str,
    run_id_2: str,
    storage: PromptLogStorage,
) -> dict[str, Any]:
    """
    Compare two runs and generate diff.

    Args:
        run_id_1: First run ID
        run_id_2: Second run ID
        storage: Storage backend

    Returns:
        Dictionary with diff results
    """
    run1 = storage.get_run(run_id_1)
    run2 = storage.get_run(run_id_2)

    if not run1 or not run2:
        raise ValueError("One or both runs not found")

    # Textual diff
    output_diff = _text_diff(
        str(run1.outputs.get("result", "")),
        str(run2.outputs.get("result", "")),
    )

    # Metrics comparison
    metrics_diff = {
        "execution_time": {
            "run1": run1.execution_time,
            "run2": run2.execution_time,
            "diff": run2.execution_time - run1.execution_time,
        },
        "tokens_used": {
            "run1": run1.tokens_used,
            "run2": run2.tokens_used,
            "diff": run2.tokens_used - run1.tokens_used,
        },
        "cost_estimate": {
            "run1": run1.cost_estimate,
            "run2": run2.cost_estimate,
            "diff": run2.cost_estimate - run1.cost_estimate,
        },
    }

    return {
        "run1_id": run_id_1,
        "run2_id": run_id_2,
        "output_diff": output_diff,
        "metrics_diff": metrics_diff,
    }


def _text_diff(text1: str, text2: str) -> dict[str, Any]:
    """Simple textual diff (placeholder for full diff implementation)."""
    return {
        "similarity": _simple_similarity(text1, text2),
        "length_diff": len(text2) - len(text1),
    }


def _simple_similarity(text1: str, text2: str) -> float:
    """Simple similarity score (placeholder)."""
    if text1 == text2:
        return 1.0

    # Simple word overlap
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0
