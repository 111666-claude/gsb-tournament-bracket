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


class ByePaddingTest(unittest.TestCase):
    def test_five_players_get_three_byes(self):
        pairs = build(["p1", "p2", "p3", "p4", "p5"])
        self.assertEqual(len(pairs), 4)
        self.assertEqual(sum(1 for first, second in pairs if second is None), 3)

    def test_every_player_exactly_once(self):
        players = ["p%d" % i for i in range(13)]
        pairs = build(players)
        placed = [name for pair in pairs for name in pair if name is not None]
        self.assertEqual(sorted(placed), sorted(players))
        self.assertEqual(len(pairs), 8)

    def test_power_of_two_has_no_bye(self):
        pairs = build(["a", "b", "c", "d"])
        self.assertEqual(pairs, [("a", "b"), ("c", "d")])


class ReplayTest(unittest.TestCase):
    def test_decided_match_rejects_second_report(self):
        pairs = build(["a", "b"])
        report(pairs, 0, "a")
        with self.assertRaises(BracketError):
            report(pairs, 0, "b")

    def test_result_is_locked_after_report(self):
        pairs = build(["a", "b"])
        report(pairs, 0, "a")
        try:
            report(pairs, 0, "b")
        except BracketError:
            pass
        self.assertEqual(pairs[0], ("a", "b"))

    def test_other_matches_still_open(self):
        pairs = build(["a", "b", "c", "d"])
        report(pairs, 0, "a")
        self.assertTrue(report(pairs, 1, "d"))

    def test_none_winner_rejected_on_bye(self):
        pairs = build(["a", "b", "c"])
        with self.assertRaises(BracketError):
            report(pairs, 1, None)


def reference_build(players):
    """参考实现：补轮空到下一个 2 的幂。"""
    size = 1
    while size < len(players):
        size *= 2
    slots = list(players) + [None] * (size - len(players))
    real = len(players) - (size - len(players))
    pairs = []
    for i in range(0, real // 2 * 2, 2):
        pairs.append((slots[i], slots[i + 1]))
    for i in range(real, size, 1):
        if slots[i] is not None:
            pairs.append((slots[i], None))
    return pairs


def reference_report(pairs, locked, index, winner):
    """参考实现：结果锁定，重复上报与非法赢家都报错。"""
    if index < 0 or index >= len(pairs):
        raise BracketError("bad index")
    if index in locked:
        raise BracketError("locked")
    first, second = pairs[index]
    if winner is None or winner not in (first, second):
        raise BracketError("bad winner")
    pairs[index] = (winner, second if winner == first else first)
    locked.add(index)


class DifferentialTest(unittest.TestCase):
    def test_random_against_reference(self):
        import random

        rng = random.Random(20260930)
        for _ in range(200):
            count = rng.randrange(0, 40)
            players = ["p%d" % i for i in range(count)]
            actual = build(players)
            expected = reference_build(players)
            self.assertEqual(list(actual), expected)
            locked = set()
            for _ in range(rng.randrange(0, 60)):
                index = rng.randrange(-1, max(1, count + 1))
                winner = rng.choice(players + ["ghost", None])
                actual_err = expected_err = None
                try:
                    report(actual, index, winner)
                except BracketError as err:
                    actual_err = err
                try:
                    reference_report(expected, locked, index, winner)
                except BracketError as err:
                    expected_err = err
                self.assertEqual(
                    (actual_err is None, list(actual)),
                    (expected_err is None, list(expected)),
                )

    def test_replay_same_batch_is_deterministic(self):
        import random

        rng = random.Random(7)
        players = ["p%d" % i for i in range(23)]
        batch = [(rng.randrange(0, 16), rng.choice(players)) for _ in range(50)]
        outcomes = []
        for _ in range(2):
            pairs = build(players)
            errors = []
            for index, winner in batch:
                try:
                    report(pairs, index, winner)
                    errors.append(False)
                except BracketError:
                    errors.append(True)
            outcomes.append((list(pairs), errors))
        self.assertEqual(outcomes[0], outcomes[1])


class ScaleTest(unittest.TestCase):
    def test_80k_players_100k_reports_under_a_second(self):
        import time

        players = ["p%d" % i for i in range(80000)]
        pairs = build(players)
        start = time.monotonic()
        for i in range(100000):
            index = i % len(pairs)
            first, _ = pairs[index]
            try:
                report(pairs, index, first)
            except BracketError:
                pass
        self.assertLess(time.monotonic() - start, 1.0)


if __name__ == "__main__":
    unittest.main()
