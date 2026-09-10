# Treaty Classification Tool

An honest, offline baseline for classifying treaty mentions. It makes no
network calls and never requires an API key.

## Stance categories

- **Supporting**: endorses the treaty, encourages ratification, or advocates implementing it.
- **Opposing**: rejects it, advocates withdrawal or blocking, or undermines it.
- **Mixed / Conditional**: supports some provisions but opposes others, or supports it only if conditions are met.
- **Neutral / Descriptive**: describes the treaty without expressing support or opposition.
- **Needs review**: insufficient or ambiguous evidence; this is the fallback, not a stance.

## Usage

Python 3.9+ is required. The classifier uses only the standard library:

```console
python Classifier.py --text "We urge parliament to ratify the treaty."
python Classifier.py speeches.txt "climate treaty" --output results.csv
```

Input files may be pipe-delimited (`speech_id|text`) or CSV with `Speech_ID`
and `Mention` (or `id` and `text`) columns. Output includes the category,
confidence score, and matched evidence so results can be reviewed.

The rule-based baseline is deterministic and intentionally conservative.
`classify_text()` returns the full `Classification` object; the legacy
`classify_treaty(text)` function remains available and returns only its category.
An LLM provider can be added behind this interface later, but no provider or
secret is required for the baseline.

## Development

Run the tests with:

```console
python -m unittest discover -s tests -v
```