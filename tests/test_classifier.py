import csv
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from Classifier import (
    MIXED_CONDITIONAL,
    NEEDS_REVIEW,
    NEUTRAL,
    OPPOSING,
    SUPPORTING,
    classify_text,
    classify_treaty,
    command_line_main,
    process_file,
)


class ClassifierTests(unittest.TestCase):
    def test_stance_categories(self):
        cases = {
            "We endorse and urge parliament to ratify the treaty.": SUPPORTING,
            "The government rejects the treaty and advocates withdrawal.": OPPOSING,
            "The government opposes withdrawal from the treaty.": SUPPORTING,
            "The government supports withdrawal from the treaty.": OPPOSING,
            "We support the treaty only if enforcement is strengthened.": MIXED_CONDITIONAL,
            "The treaty agreement was signed in 2020 by three parties.": NEUTRAL,
            "The treaty is important.": NEEDS_REVIEW,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(classify_treaty(text, target="treaty"), expected)

    def test_result_exposes_deterministic_evidence(self):
        first = classify_text("We encourage implementation of the treaty.", target="treaty")
        second = classify_text("We encourage implementation of the treaty.", target="treaty")
        self.assertEqual(first, second)
        self.assertTrue(first.evidence)
        self.assertGreater(first.rule_score, 0)

    def test_file_processing_and_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "speeches.txt"
            path.write_text("id|text\n1|We support the treaty.\n2|Unrelated text.\n", encoding="utf-8")
            rows = process_file(str(path), "treaty")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["Category"], SUPPORTING)
            with self.assertRaises(ValueError):
                process_file(str(path), "", 1)

    def test_headered_pipe_input_keeps_first_data_record(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "speeches.txt"
            path.write_text(
                "id|text\n1|We support the treaty.\n2|We oppose the treaty.\n",
                encoding="utf-8",
            )
            rows = process_file(str(path), "treaty")
            self.assertEqual([row["Speech_ID"] for row in rows], ["1", "2"])

    def test_headerless_pipe_input_does_not_duplicate_first_record(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "speeches.txt"
            path.write_text(
                "1|We support the treaty.\n2|We oppose the treaty.\n",
                encoding="utf-8",
            )
            rows = process_file(str(path), "treaty")
            self.assertEqual([row["Speech_ID"] for row in rows], ["1", "2"])

    def test_invalid_csv_headers_fail_clearly(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.csv"
            path.write_text("speaker,statement\n1,We support the treaty.\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid CSV headers"):
                process_file(str(path), "treaty")

    def test_cli_text_and_csv_output(self):
        self.assertEqual(command_line_main(["--text", "We oppose withdrawal from the treaty."]), 0)
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.txt"
            output_path = Path(directory) / "output.csv"
            input_path.write_text("id|text\n1|We support the treaty.\n", encoding="utf-8")
            self.assertEqual(command_line_main([str(input_path), "treaty", "-o", str(output_path)]), 0)
            with output_path.open(newline="", encoding="utf-8") as handle:
                self.assertEqual(next(csv.DictReader(handle))["Category"], SUPPORTING)

    def test_withdrawal_stance_is_target_aware_and_not_ambiguous(self):
        opposing_withdrawal = classify_text("The government supports withdrawal from the treaty.", "treaty")
        supporting_withdrawal = classify_text("The government opposes withdrawal from the treaty.", "treaty")

        self.assertEqual(opposing_withdrawal.category, OPPOSING)
        self.assertEqual(supporting_withdrawal.category, SUPPORTING)
        self.assertNotEqual(opposing_withdrawal.category, NEEDS_REVIEW)
        self.assertNotEqual(supporting_withdrawal.category, NEEDS_REVIEW)

    def test_negated_support_is_opposing(self):
        result = classify_text("We do not support the treaty.", "treaty")
        self.assertEqual(result.category, OPPOSING)

    def test_negated_opposition_remains_conservative(self):
        result = classify_text("We do not oppose the treaty.", "treaty")
        self.assertEqual(result.category, NEEDS_REVIEW)

    def test_generic_treaty_vocabulary_cannot_outscore_explicit_stance(self):
        result = classify_text("The treaty agreement was signed, but we reject the treaty.", "treaty")
        self.assertEqual(result.category, OPPOSING)

    def test_quoted_views_are_not_treated_as_direct_stance(self):
        result = classify_text('The minister quoted, "We support the treaty."', "treaty")
        self.assertEqual(result.category, NEEDS_REVIEW)

    def test_unrelated_sentiment_does_not_attach_to_target(self):
        result = classify_text("I oppose the policy. The treaty was signed in 2020.", "treaty")
        self.assertEqual(result.category, NEUTRAL)

    def test_single_text_requires_explicit_target(self):
        self.assertEqual(classify_text("We support the treaty.").category, NEEDS_REVIEW)
        self.assertEqual(
            classify_text("We support the Paris Agreement.", "Paris Agreement").category,
            SUPPORTING,
        )
        self.assertEqual(
            classify_text("We support the Paris Agreement.", "Kyoto Protocol").category,
            NEEDS_REVIEW,
        )

    def test_evidence_is_exact_and_explanations_are_separate(self):
        result = classify_text("We SUPPORT the Treaty.", "treaty")
        self.assertEqual(result.evidence, ("SUPPORT",))
        self.assertTrue(result.rule_explanations)
        self.assertNotIn(":", result.evidence[0])

    def test_sample_output_matches_generated_output(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "sample_output.csv"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    command_line_main(
                        ["sample_input.txt", "treaty", "--output", str(output_path)]
                    ),
                    0,
                )
            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                (root / "sample_output.csv").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
