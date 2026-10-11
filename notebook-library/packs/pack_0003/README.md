# Prompt Evaluation Harness

## What Problem This Pack Solves

Evaluating prompt performance manually requires running tests, collecting responses, scoring quality, and tracking changes over time—a labor-intensive process prone to inconsistency. This pack eliminates that friction by automating prompt evaluation, scoring across multiple metrics, and detecting performance drift between prompt versions.

## What You Get

- **Prompt Scoring** - Automated evaluation metrics for prompt performance and quality (clarity, specificity, completeness, relevance)
- **Drift Detection** - Identify when prompt performance degrades or improves between versions
- **Evaluation Reports** - Comprehensive markdown reports with scores and comparisons

## How It Works

The notebook follows a deterministic, step-by-step process:

1. **Configuration** - Sets input/output paths and evaluation metrics
2. **Environment Validation** - Checks Python version, required packages, and write permissions
3. **Input Loading** - Loads prompts JSON or generates sample prompts if not provided
4. **Prompt Evaluation** - Scores each prompt across multiple metrics
5. **Drift Detection** - Compares versions to detect performance changes
6. **Output Writing** - Saves evaluation results JSON and report markdown to outputs directory

The notebook is designed to run top-to-bottom without any hidden state or dependencies on prior executions. All randomness is seeded for deterministic results.

## Inputs Required

### Required
- None (pack generates sample prompts if input not provided)

### Optional
- `data/prompts.json` - Your prompts data (will generate sample if not provided)
  ```json
  {
    "prompts": [
      {
        "id": "prompt_001",
        "text": "Your prompt text here",
        "category": "summarization",
        "version": "1.0"
      }
    ]
  }
  ```

### Example Inputs

```bash
# Create your prompts file
cat > data/prompts.json << EOF
{
  "prompts": [
    {
      "id": "my_prompt",
      "text": "Summarize the following text",
      "category": "summarization",
      "version": "1.0"
    }
  ]
}
EOF
```

## Outputs Produced

All outputs are written to the `outputs/` directory:

1. **`outputs/evaluation_results.json`** - Complete evaluation scores and metrics
   ```json
   {
     "evaluations": [
       {
         "prompt_id": "prompt_001",
         "scores": {
           "clarity": 0.85,
           "specificity": 0.72,
           "completeness": 0.90,
           "relevance": 0.88,
           "overall": 0.84
         }
       }
     ],
     "drift_detection": {...}
   }
   ```

2. **`outputs/evaluation_report.md`** - Summary report with scores and drift analysis

## Common Failure Modes + Fixes

### Error: "Python 3.10+ required"
**Fix:** Upgrade Python to 3.10 or higher. Check version with `python --version`.

### Error: "Required package not installed"
**Fix:** Install dependencies: `pip install -r requirements.txt`

### Error: "Cannot write to outputs"
**Fix:** Ensure write permissions in the current directory. Run `chmod u+w .` if needed.

### Error: "Input prompts file is empty or invalid"
**Fix:** Ensure your prompts.json has a "prompts" array with at least one prompt object.

### Note: Evaluation Method
**Important:** This pack uses rule-based evaluation for demonstration. In production, replace with actual LLM-based evaluation or use external evaluation APIs.

## License + Support Expectations

- **License:** GPL-3.0-only (see LICENSE.txt)
- **Support:** This is a commercial pack sold through the Keys marketplace. Support is provided through the marketplace platform.
- **Warranty:** Pack is provided "as-is" without warranty. Test in a development environment before production use.

## This Pack Is For

- Prompt engineers evaluating prompt performance
- Teams tracking prompt quality over time
- Developers building prompt testing pipelines
- Researchers studying prompt effectiveness

## This Pack Is NOT For

- Complete beginners to Python (requires Python 3.10+ knowledge)
- Users needing real-time LLM evaluation (this uses rule-based scoring)
- Projects requiring proprietary/closed-source licensing (pack is GPL-3.0)
- Users who need production LLM integration (requires customization)

## Technical Details

- **Runtime:** ~20 minutes (depends on number of prompts)
- **Dependencies:** pandas, numpy (see requirements.txt)
- **Deterministic:** Yes - all randomness seeded, no hidden state
- **Idempotent:** Yes - can be run multiple times safely (overwrites outputs)
- **Evaluation Method:** Rule-based (replace with LLM evaluation for production)

## Next Steps After Running

1. Review `outputs/evaluation_report.md` for scores and insights
2. Check `outputs/evaluation_results.json` for detailed metrics
3. Integrate with LLM APIs for production evaluation
4. Set up automated evaluation pipelines for continuous monitoring

---

**Version:** 1.1.0  
**Last Updated:** 2026-10-11
