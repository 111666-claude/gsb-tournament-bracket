import unittest

from tournamentbracket.bracket import BracketError, build, bye_count, report


class BuildTest(unittest.TestCase):
    def test_even_players(self):
        self.assertEqual(len(build(["a", "b", "c", "d"])), 2)

    def test_odd_players_get_a_pair(self):
        self.assertEqual(len(build(["a", "b", "c"])), 2)

    def test_bye_count_for_five(self):
        self.assertEqual(bye_count(["a"] * 5), 3)

    def test_bye_count_for_four(self):
        self.assertEqual(bye_count(["a"] * 4), 0)


class ReportTest(unittest.TestCase):
    def test_bad_index(self):
        with self.assertRaises(BracketError):
            report(build(["a", "b"]), 5, "a")

    def test_winner_must_be_in_match(self):
        with self.assertRaises(BracketError):
            report(build(["a", "b"]), 0, "z")


if __name__ == "__main__":
    unittest.main()
