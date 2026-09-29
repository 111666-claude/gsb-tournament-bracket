import random
import time
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

    def test_five_players_get_three_byes(self):
        pairs = build(["p1", "p2", "p3", "p4", "p5"])
        self.assertEqual(len(pairs), 4)
        byes = [pair for pair in pairs if pair[1] is None]
        self.assertEqual(len(byes), 3)
        self.assertEqual([pair[0] for pair in byes], ["p3", "p4", "p5"])

    def test_first_pair_is_a_real_match(self):
        pairs = build(["p1", "p2", "p3", "p4", "p5"])
        self.assertEqual(pairs[0], ("p1", "p2"))

    def test_bye_counts_for_every_size(self):
        for count in range(2, 66):
            players = ["p%d" % i for i in range(count)]
            pairs = build(players)
            byes = sum(1 for pair in pairs if pair[1] is None)
            self.assertEqual(byes, bye_count(players))
            self.assertEqual(len(pairs) * 2, count + byes)

    def test_each_player_appears_exactly_once(self):
        players = ["p%d" % i for i in range(13)]
        positions = [slot for pair in build(players) for slot in pair if slot is not None]
        self.assertEqual(sorted(positions), sorted(players))

    def test_power_of_two_has_no_bye(self):
        for count in (2, 4, 8, 16, 32):
            pairs = build(["p%d" % i for i in range(count)])
            self.assertEqual(sum(1 for pair in pairs if pair[1] is None), 0)
            self.assertEqual(len(pairs), count // 2)

    def test_duplicate_registration_rejected(self):
        with self.assertRaises(BracketError):
            build(["a", "b", "a"])

    def test_tiny_fields(self):
        self.assertEqual(build([]), [])
        self.assertEqual(build(["only"]), [])
        self.assertEqual(bye_count([]), 0)
        self.assertEqual(bye_count(["only"]), 0)


class ReportTest(unittest.TestCase):
    def test_bad_index(self):
        with self.assertRaises(BracketError):
            report(build(["a", "b"]), 5, "a")

    def test_winner_must_be_in_match(self):
        with self.assertRaises(BracketError):
            report(build(["a", "b"]), 0, "z")

    def test_negative_index(self):
        with self.assertRaises(BracketError):
            report(build(["a", "b"]), -1, "a")

    def test_repeated_report_is_locked(self):
        pairs = build(["a", "b", "c", "d"])
        self.assertTrue(report(pairs, 0, "a"))
        self.assertEqual(pairs[0], ("a", "b"))
        with self.assertRaises(BracketError):
            report(pairs, 0, "b")
        self.assertEqual(pairs[0], ("a", "b"))

    def test_same_winner_twice_is_still_locked(self):
        pairs = build(["a", "b"])
        report(pairs, 0, "a")
        with self.assertRaises(BracketError):
            report(pairs, 0, "a")

    def test_reporting_bye_match(self):
        pairs = build(["a", "b", "c"])
        self.assertEqual(pairs[1], ("c", None))
        report(pairs, 1, "c")
        self.assertEqual(pairs[1], ("c", None))
        with self.assertRaises(BracketError):
            report(pairs, 1, "c")
        with self.assertRaises(BracketError):
            report(pairs, 1, "a")

    def test_batch_replay_is_stable(self):
        events = [(0, "a"), (1, "c")]
        first = build(["a", "b", "c", "d"])
        for index, winner in events:
            report(first, index, winner)
        snapshot = list(first)
        second = build(["a", "b", "c", "d"])
        for index, winner in events:
            report(second, index, winner)
        self.assertEqual(list(second), snapshot)
        with self.assertRaises(BracketError):
            for index, winner in events:
                report(second, index, winner)
        self.assertEqual(list(second), snapshot)


class ScaleTest(unittest.TestCase):
    def test_eighty_thousand_players(self):
        players = ["p%d" % i for i in range(80000)]
        start = time.perf_counter()
        pairs = build(players)
        byes = sum(1 for pair in pairs if pair[1] is None)
        self.assertEqual(byes, 131072 - 80000)
        reports = 0
        for index, pair in enumerate(pairs):
            if pair[1] is not None:
                report(pairs, index, pair[0])
                reports += 1
        while reports < 100000:
            with self.assertRaises(BracketError):
                report(pairs, 0, pairs[0][0])
            reports += 1
        self.assertLess(time.perf_counter() - start, 1.0)


class ReferenceMatchTest(unittest.TestCase):
    """随机 200 组：与「补轮空 + 结果锁定」的独立参考实现逐项对照。"""

    def test_random_brackets_match_reference(self):
        rng = random.Random(20260930)
        for _ in range(200):
            self._run_one_case(rng)

    def _run_one_case(self, rng):
        count = rng.choice(
            [0, 1, 2, 3, 4, 5, 6, 7, 8]
            + [rng.randrange(0, 80) for _ in range(8)]
        )
        names = ["n%d" % i for i in range(count)]
        if count and rng.random() < 0.1:
            names[rng.randrange(count)] = names[rng.randrange(count)]

        reference = _ReferenceBracket(names)
        if reference.duplicate:
            with self.assertRaises(BracketError):
                build(names)
            return

        production = _ProductionBracket(names)
        self.assertEqual(
            [tuple(pair) for pair in production.rounds[0]],
            [tuple(pair) for pair in reference.rounds[0]],
        )

        steps = rng.randrange(0, 40)
        for _ in range(steps):
            kind, round_index, match_index, winner = self._next_event(rng, reference)
            expected = reference.submit(round_index, match_index, winner)
            actual = production.submit(round_index, match_index, winner)
            self.assertEqual(actual, expected)
            for round_index, pairs in enumerate(production.rounds):
                self.assertEqual(
                    [tuple(pair) for pair in pairs],
                    [tuple(pair) for pair in reference.rounds[round_index]],
                )
                self.assertEqual(set(pairs.decided), reference.locked[round_index])

        self.assertEqual(production.champion(), reference.champion())

    def _next_event(self, rng, reference):
        open_matches = reference.open_matches()
        locked_matches = reference.locked_matches()
        roll = rng.random()
        if roll < 0.65 and open_matches:
            round_index, match_index = rng.choice(open_matches)
            return ("play", round_index, match_index,
                    reference.rounds[round_index][match_index][0])
        if roll < 0.75 and open_matches:
            round_index, match_index = rng.choice(open_matches)
            first, second = reference.rounds[round_index][match_index]
            stranger = "stranger%d" % rng.randrange(100000)
            while stranger in (first, second):
                stranger += "x"
            return ("bad_winner", round_index, match_index, stranger)
        if locked_matches:
            round_index, match_index = rng.choice(locked_matches)
            first, second = reference.rounds[round_index][match_index]
            winner = first if rng.random() < 0.5 else (second or first)
            return ("replay", round_index, match_index, winner)
        if rng.random() < 0.5:
            return ("bad_index", len(reference.rounds), 0, "x")
        if open_matches:
            round_index, match_index = rng.choice(open_matches)
            return ("play", round_index, match_index,
                    reference.rounds[round_index][match_index][0])
        return ("bad_index", 0, 999, "x")


def _reference_first_round(names):
    """独立参考实现：先填满 2 的幂个签位，再按相邻签位两两配对。"""
    count = len(names)
    if count < 2:
        return [], 0
    size = 1
    while size < count:
        size *= 2
    total_matches = size // 2
    real_matches = total_matches - (size - count)
    slots = [None] * size
    queue = list(names)
    for match in range(total_matches):
        slots[2 * match] = queue.pop(0)
        if match < real_matches:
            slots[2 * match + 1] = queue.pop(0)
    pairs = [(slots[i], slots[i + 1]) for i in range(0, size, 2)]
    return [list(pair) for pair in pairs], total_matches


class _ReferenceBracket:
    def __init__(self, names):
        self.duplicate = len(set(names)) != len(names)
        if self.duplicate:
            return
        first_round, _ = _reference_first_round(names)
        self.rounds = [first_round]
        self.locked = [set()]
        self.sole = names[0] if len(names) == 1 else None
        self._settle()

    def _winner(self, round_index, match_index):
        pair = self.rounds[round_index][match_index]
        if match_index in self.locked[round_index]:
            return pair[0]
        if pair[1] is None:
            return pair[0]
        return None

    def _settle(self):
        while True:
            round_index = len(self.rounds) - 1
            pairs = self.rounds[round_index]
            if len(pairs) <= 1:
                return
            winners = []
            for match_index in range(0, len(pairs), 2):
                left = self._winner(round_index, match_index)
                right = self._winner(round_index, match_index + 1)
                if left is None or right is None:
                    return
                winners.append((left, right))
            self.rounds.append([list(pair) for pair in winners])
            self.locked.append(set())

    def submit(self, round_index, match_index, winner):
        if not (0 <= round_index < len(self.rounds)):
            return "bad_index"
        pairs = self.rounds[round_index]
        if not (0 <= match_index < len(pairs)):
            return "bad_index"
        if match_index in self.locked[round_index]:
            return "over"
        first, second = pairs[match_index]
        if winner not in (first, second):
            return "bad_winner"
        pairs[match_index] = [winner, second if winner == first else first]
        self.locked[round_index].add(match_index)
        self._settle()
        return "ok"

    def open_matches(self):
        result = []
        for round_index, pairs in enumerate(self.rounds):
            for match_index, pair in enumerate(pairs):
                if pair[1] is not None and match_index not in self.locked[round_index]:
                    result.append((round_index, match_index))
        return result

    def locked_matches(self):
        result = []
        for round_index, locked in enumerate(self.locked):
            for match_index in locked:
                result.append((round_index, match_index))
        return result

    def champion(self):
        if self.duplicate:
            return None
        if self.sole is not None:
            return self.sole
        last = len(self.rounds) - 1
        if len(self.rounds[last]) == 1 and 0 in self.locked[last]:
            return self.rounds[last][0][0]
        return None


class _ProductionBracket:
    def __init__(self, names):
        self.rounds = [build(names)]
        self.sole = names[0] if len(names) == 1 else None
        self._settle()

    def _winner(self, round_index, match_index):
        pairs = self.rounds[round_index]
        pair = pairs[match_index]
        if match_index in pairs.decided:
            return pair[0]
        if pair[1] is None:
            return pair[0]
        return None

    def _settle(self):
        while True:
            round_index = len(self.rounds) - 1
            pairs = self.rounds[round_index]
            if len(pairs) <= 1:
                return
            winners = []
            for match_index in range(0, len(pairs), 2):
                left = self._winner(round_index, match_index)
                right = self._winner(round_index, match_index + 1)
                if left is None or right is None:
                    return
                winners.append(left)
                winners.append(right)
            self.rounds.append(build(winners))

    def submit(self, round_index, match_index, winner):
        if not (0 <= round_index < len(self.rounds)):
            return "bad_index"
        pairs = self.rounds[round_index]
        if not (0 <= match_index < len(pairs)):
            return "bad_index"
        try:
            report(pairs, match_index, winner)
        except BracketError as error:
            text = error.message
            if "已经" in text:
                return "over"
            if "不在" in text:
                return "bad_winner"
            return "bad_index"
        self._settle()
        return "ok"

    def champion(self):
        if self.sole is not None:
            return self.sole
        last = len(self.rounds) - 1
        pairs = self.rounds[last]
        if len(pairs) == 1 and 0 in pairs.decided:
            return pairs[0][0]
        return None


if __name__ == "__main__":
    unittest.main()
