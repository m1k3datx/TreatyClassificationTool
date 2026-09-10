import csv
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
            "We support the treaty only if enforcement is strengthened.": MIXED_CONDITIONAL,
            "The agreement was signed in 2020 by three parties.": NEUTRAL,
            "The treaty is important.": NEEDS_REVIEW,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(classify_treaty(text), expected)

    def test_result_exposes_deterministic_evidence(self):
        first = classify_text("We encourage implementation of the treaty.")
        second = classify_text("We encourage implementation of the treaty.")
        self.assertEqual(first, second)
        self.assertTrue(first.evidence)
        self.assertGreater(first.confidence, 0)

    def test_file_processing_and_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "speeches.txt"
            path.write_text("id|text\n1|We support the treaty.\n2|Unrelated text.\n", encoding="utf-8")
            rows = process_file(str(path), "treaty")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["Category"], SUPPORTING)
            with self.assertRaises(ValueError):
                process_file(str(path), "", 1)

    def test_cli_text_and_csv_output(self):
        self.assertEqual(command_line_main(["--text", "We oppose withdrawal from the treaty."]), 0)
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.txt"
            output_path = Path(directory) / "output.csv"
            input_path.write_text("id|text\n1|We support the treaty.\n", encoding="utf-8")
            self.assertEqual(command_line_main([str(input_path), "treaty", "-o", str(output_path)]), 0)
            with output_path.open(newline="", encoding="utf-8") as handle:
                self.assertEqual(next(csv.DictReader(handle))["Category"], SUPPORTING)


if __name__ == "__main__":
    unittest.main()
