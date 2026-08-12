import string
import unittest

from player.strings import LANGUAGES, Strings, get, language_names


class TestStrings(unittest.TestCase):
    def test_same_keys_in_all_languages(self):
        reference = set(LANGUAGES["fa"])
        for code, table in LANGUAGES.items():
            self.assertEqual(
                reference,
                set(table),
                msg=f"کلیدهای زبان {code} با فارسی یکسان نیست",
            )

    def test_same_placeholders(self):
        formatter = string.Formatter()

        def placeholders(text: str) -> set[str]:
            return {name for _, name, _, _ in formatter.parse(text) if name}

        for key, persian in LANGUAGES["fa"].items():
            for code, table in LANGUAGES.items():
                self.assertEqual(
                    placeholders(persian),
                    placeholders(table[key]),
                    msg=f"جای‌گذاری‌های کلید {key} در زبان {code} همخوان نیست",
                )

    def test_get_formats(self):
        text = get("volume_set", "fa", volume=80)
        self.assertIn("80", text)

    def test_missing_placeholder_does_not_raise(self):
        self.assertIsInstance(get("volume_set", "fa"), str)

    def test_unknown_key_returns_key(self):
        self.assertEqual(get("this_key_does_not_exist", "fa"), "this_key_does_not_exist")

    def test_unknown_language_falls_back(self):
        s = Strings("de")
        self.assertIn(s.language, LANGUAGES)

    def test_language_names(self):
        self.assertEqual(set(language_names()), set(LANGUAGES))


if __name__ == "__main__":
    unittest.main()
