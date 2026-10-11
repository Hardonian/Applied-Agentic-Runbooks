# Changelog

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-10-11

### Added
- Complete production-ready executable `main.ipynb` with 11-step pipeline
- Pre-populated benchmark dataset in `data/prompts.json` across 3 agent domains
- Automated multi-dimensional scoring engine (Clarity, Specificity, Completeness, Relevance, Safety)
- Statistical version drift calculation ($\Delta$) with regression/improvement classification
- Automated markdown report generation in `outputs/evaluation_report.md`
- Complete verified JSON serialization in `outputs/evaluation_results.json`

## [1.0.0] - 2026-01-04

### Added
- Initial pack specification and schema definition
- Prompt evaluation specification across multiple metrics
- Documentation templates (README, quickstart)

### Changed
- N/A

### Fixed
- N/A

### Removed
- N/A

### Note
- Uses rule-based evaluation for demonstration. Replace with LLM-based evaluation for production use.
