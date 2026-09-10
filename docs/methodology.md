# Methodology notes

The current tool is an offline review aid, not a reconstruction of the original statistical study. It searches each input record for an explicit target phrase, isolates sentences containing that target, and applies deterministic regular-expression rules for supporting, opposing, mixed/conditional, and neutral/descriptive language.

Each result includes the selected category, an uncalibrated rule score, exact evidence excerpts copied from the input, and explanations identifying the configured rules that matched. If the target is absent, the text is empty, or evidence is weak or ambiguous, the tool returns `Needs review`.

The original presentation used the comparative research workflow described in the [case study](case-study.md). Current software tests document implementation behavior only; they do not establish research validity or reproduce the original presentation's reported relationship.
