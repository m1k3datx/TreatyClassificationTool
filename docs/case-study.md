# Case study: Who Commits, Who Talks?

## Research question

The project asks whether stronger legal commitment to international treaties corresponds with greater rhetorical engagement in legislative discourse. “Engagement” here means the presence and classification of treaty mentions; mention counts do not establish legislative intent, compliance, or symbolic behavior. Those are interpretations and research questions for further study.

## Original presentation scope

The poster examined 10 democracies, eight major treaties, and the period 1990–2017. The presentation named ParlSpeech V2 and the Congressional Record collection as sources. Its workflow was to extract treaty mentions, compare discourse with treaty commitment, and present the results.

The original-presentation finding was that the observed relationship was sensitive to including the United States. This statement describes the presentation's reported comparison; it is not a claim that the current software reproduced its statistical results.

## Contribution and software evolution

The contribution was to connect legal treaty commitment with legislative rhetoric in a comparative research workflow. The repository now provides a transparent, offline implementation for reviewing treaty mentions: explainable stance rules, target-aware matching, input validation, exact evidence excerpts, conservative `Needs review` fallbacks, automated tests, and continuous integration.

The current tests check software behavior such as rule outcomes, evidence determinism, input validation, CSV/pipe-delimited parsing, and CLI serialization. They do not reproduce or validate the original presentation's statistical analysis.

## Limitations and future work

The current classifier is an uncalibrated rule-based baseline. It can miss context, irony, indirect language, speaker attribution, and treaty aliases, and it should not be treated as a measure of intent, compliance, or symbolic behavior. Future work could add a documented coding protocol, richer metadata and treaty-identity resolution, human validation, calibrated evaluation, and a separate replication of the original comparative analysis.
