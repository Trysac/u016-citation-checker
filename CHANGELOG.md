# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added `split_claims` and `check_citations` to verify that each claim of a RAG answer is supported by the passages it cites (lexical and numeric checks, optional capped LLM judge for borderline claims), with `LLMPort`, `RecordedLLM`, `FakeLLM` and the typed `CitationError`.
- Initial project structure from the factory utility template.
