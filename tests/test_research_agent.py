import unittest
from unittest.mock import AsyncMock

from research_agent import Judgment, analyze, make_report, markdown_report, reconcile


class ResearchTests(unittest.IsolatedAsyncioTestCase):
    source = "We support the Paris Agreement."

    def judgment(self, category="Supporting", evidence=None):
        return Judgment(category=category, evidence=evidence or [self.source],
                        explanation="The speaker states a position.")

    def test_matching_labels_with_exact_evidence(self):
        result = reconcile(self.source, self.judgment(), self.judgment())
        self.assertEqual(result["category"], "Supporting")

    def test_fabricated_evidence_requires_review(self):
        result = reconcile(self.source, self.judgment(), self.judgment(evidence=["Invented quote"]))
        self.assertEqual(result["category"], "Needs review")
        self.assertEqual(result["evidence"], [])
        self.assertFalse(result["checks"]["review_exact_evidence"])

    def test_disagreement_never_automatically_overrides(self):
        result = reconcile(self.source, self.judgment(), self.judgment("Opposing"))
        self.assertEqual(result["category"], "Needs review")
        self.assertFalse(result["checks"]["category_agreement"])

    def test_empty_evidence_requires_review(self):
        draft = self.judgment()
        draft.evidence = []
        self.assertEqual(reconcile(self.source, draft, self.judgment())["category"], "Needs review")

    async def test_two_passes_preserve_source_and_report_counts(self):
        judge = AsyncMock(side_effect=[self.judgment(), self.judgment()])
        row = {"id": "synthetic", **await analyze(self.source, "Paris Agreement", judge)}
        self.assertEqual(judge.await_count, 2)
        self.assertEqual(judge.await_args_list[1].args[0], "review")
        self.assertEqual(row["source"], self.source)
        report = make_report([row], "Paris Agreement", "test-model")
        self.assertEqual(report["category_counts"]["Supporting"], 1)
        self.assertIn("Passages analyzed: 1", markdown_report(report))

    async def test_provider_error_propagates(self):
        judge = AsyncMock(side_effect=RuntimeError("Provider unavailable"))
        with self.assertRaises(RuntimeError):
            await analyze(self.source, "Paris Agreement", judge)
        self.assertEqual(judge.await_count, 1)

    async def test_oversize_input_never_calls_provider(self):
        judge = AsyncMock()
        with self.assertRaises(ValueError):
            await analyze("x" * 30001, "Paris Agreement", judge)
        judge.assert_not_called()


if __name__ == "__main__":
    unittest.main()
