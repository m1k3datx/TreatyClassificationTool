# Methodology notes

The current tool offers two explicit modes and is not a reconstruction of the original statistical study. `--offline-baseline` searches each input record for an explicit target phrase, isolates sentences containing that target, and applies deterministic regular-expression rules for supporting, opposing, mixed/conditional, and neutral/descriptive language. `--ai` sends the selected passage and explicit target to Gemini for contextual analysis.

Each baseline result includes the selected category, an uncalibrated rule score, exact evidence excerpts copied from the input, and explanations identifying the configured rules that matched. AI results include a provider score, explanation, and evidence excerpts. AI JSON is validated against the allowed categories and evidence must be an exact substring of the source; malformed responses, missing evidence, and provider errors are surfaced rather than converted to baseline results. The prompt covers quoted/unrelated speech, negation, withdrawal, and conditional language without claiming perfect accuracy.

AI mode requires `GEMINI_API_KEY` in the local environment and sends speech text to Gemini. Keys must not be committed or uploaded. Tests mock the provider boundary and make no network calls.

The original presentation used the comparative research workflow described in the [case study](case-study.md). Current software tests document implementation behavior only; they do not establish research validity or reproduce the original presentation's reported relationship.
