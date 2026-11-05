import unittest

from handlers.text_processor import split_text


class SplitTextTests(unittest.TestCase):
    def test_splits_long_phrases_to_word_limit(self) -> None:
        segments = split_text("Bir ikki uch to'rt besh olti", max_words=2)
        self.assertEqual(segments, ["Bir ikki", "uch to'rt", "besh olti"])

    def test_empty_text_returns_no_segments(self) -> None:
        self.assertEqual(split_text("  "), [])

    def test_rejects_non_positive_word_limit(self) -> None:
        with self.assertRaises(ValueError):
            split_text("text", max_words=0)


if __name__ == "__main__":
    unittest.main()
