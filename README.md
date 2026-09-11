# Treaty Classification Tool

[![CI](https://github.com/m1k3datx/TreatyClassificationTool/actions/workflows/ci.yml/badge.svg)](https://github.com/m1k3datx/TreatyClassificationTool/actions/workflows/ci.yml)

Developed a Python treaty-analysis workflow used in my research project, Who Commits, Who Talks?, examining the relationship between international treaty commitment and legislative discourse. The project has since been improved with explainable classification rules, input validation, automated tests, and continuous integration.

![Preview of the original research poster](docs/research/original-research-poster-preview.svg)

## Research background

The research project asks whether countries that make stronger legal commitments to international treaties also engage with those treaties more actively in legislative discourse. The original presentation compared treaty commitment and treaty mentions across democracies, using the scope and sources documented in the [case study](docs/case-study.md).

## What the current tool does

Choose OpenAI analysis with a second review pass and a final report, Gemini contextual classification, or the offline rules baseline. AI modes send the selected passages to their respective provider; offline mode requires no key. All use the same stance categories.

### OpenAI research workflow

The OpenAI Agents SDK runs a bounded classification-and-review workflow. Python checks that evidence appears verbatim in the source. Disagreement, invalid quotations, or uncertain classifications go to `Needs review`. The report includes source passages, both judgments, verification checks, counts, model name, prompt version, and source hashes. AI agreement is not human validation.

Use Python 3.12 or newer and install `requirements.txt`, then configure `OPENAI_API_KEY` in your environment or a local `.env.local` file. This file and generated `reports/` are ignored by Git. Never upload keys. Each person running the public project supplies their own key and pays their provider's API charges. See [validation status](VALIDATION.md) for test results and live-service limitations.

```console
python research_agent.py --text "We support the Paris Agreement." --target "Paris Agreement" --model gpt-6-astra --output reports/example
python research_agent.py --file speeches.txt --target "Paris Agreement" --model gpt-6-astra --limit 3 --output reports/batch
```

Set `OPENAI_MODEL` to avoid repeating `--model`. Choose a model available to your account; there is no hidden model fallback. Each passage makes two model calls, with retries disabled and output tokens bounded. The default limit is ten passages. Existing reports are not overwritten. A provider failure stops the run with an error; it never substitutes offline output or publishes a partial report as complete.

Outputs are a readable Markdown report and a JSON audit record. File mode selects literal target matches; aliases need preprocessing or explicit single-passage analysis. Selected text is sent to OpenAI. SDK tracing is disabled and response storage is requested off; provider retention policies still apply. This CLI does not deploy a public website.

Built using the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) and Responses API. The SDK keeps orchestration in this Python application; it is distinct from OpenAI's hosted Agents API. Automated tests cover evidence rejection, disagreement, report counts and provider failures, not research accuracy.

### Gemini AI mode

Install the supported Google Gen AI SDK and configure a key locally (never upload it to GitHub or commit it):

```console
python -m pip install -r requirements.txt
set GEMINI_API_KEY=your-key           # Windows PowerShell: $env:GEMINI_API_KEY="your-key"
python Classifier.py --ai --text "We support the Paris Agreement." --target "Paris Agreement"
python Classifier.py --ai speeches.txt "Paris Agreement" --output ai-results.csv
```

Use `--offline-baseline` for the explicit deterministic comparison workflow (it is also the default for backward compatibility):

```console
python Classifier.py --offline-baseline speeches.txt "Paris Agreement" --output baseline.csv
```

AI responses are constrained to JSON, checked against the allowed categories, and rejected unless every evidence excerpt is an exact non-empty substring of the source passage. Provider failures, missing keys, quota/network errors, malformed responses, and validation failures return an error; AI mode never silently falls back to rules. The prompt directs Gemini to consider target context, quoted or unrelated speech, negation, withdrawal/exit, and conditional language, but this is not a claim of perfect accuracy. AI mode is a local-user workflow and sends the selected speech passage to Google's Gemini service.

## Synthetic example

The following is intentionally synthetic and does not represent a research observation:

```text
Input:  We urge parliament to ratify the Aurora Climate Treaty.
Target: Aurora Climate Treaty
Output: Supporting
Evidence: urge parliament to ratif, ratify
```

Reproduce the example with the current CLI:

```console
python Classifier.py --text "We urge parliament to ratify the Aurora Climate Treaty." --target "Aurora Climate Treaty"
```

The generated output is preserved in [`docs/demo/synthetic-classification-output.txt`](docs/demo/synthetic-classification-output.txt).

## Quick start

The offline baseline uses only the Python standard library; AI mode additionally requires the Google Gen AI SDK from requirements.txt.

```console
python Classifier.py --offline-baseline --text "We urge parliament to ratify the Paris Agreement." --target "Paris Agreement"
python Classifier.py speeches.txt "climate treaty" --output results.csv
python -m unittest discover -s tests -v
```

Input files may be pipe-delimited (`speech_id|text`) or CSV with `Speech_ID` and `Mention` (or `id` and `text`) columns. File processing uses the search term as the target; single-text classification requires an explicit `target`.

## Project documentation

- [Case study](docs/case-study.md): research context, scope, contribution, and limitations.
- [Methodology notes](docs/methodology.md): AI response validation, baseline workflow, and review boundaries.
- [Original research poster](docs/research/original-research-poster.pdf) and [readable preview](docs/research/original-research-poster-preview.svg).
- [Tests](tests/test_classifier.py).

## Limitations

The AI workflows and offline baseline are research aids, not calibrated measures of intent, compliance, or symbolic behavior. Results depend on the supplied target phrase and source text. Human-coded evaluation is needed to measure accuracy; automated evidence checks and a second AI pass cannot establish it.

### Model selection and verification

AI mode uses `--model`, then `GEMINI_MODEL`, then `gemini-3.6-flash`. Example:

```console
python Classifier.py --ai --model gemini-3.6-flash speeches.txt "Paris Agreement" --limit 3
```

`--limit` stops after that many matching records, including AI requests; zero means all. Model access depends on your account. The default follows Google's replacement for retired Gemini 2.0 Flash, checked September 10, 2026: [Google model lifecycle](https://ai.google.dev/gemini-api/docs/deprecations). Mocked tests do not verify a real API request or classification accuracy. AI scores are model-generated, uncalibrated estimates, not validated probabilities.
