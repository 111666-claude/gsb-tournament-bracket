"""淘汰赛对阵：轮空、种子与结果上报。"""


class BracketError(ValueError):
    """输入不合法。"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class Bracket(list):
    """首轮对阵列表，附带已决出胜负的场次下标。"""

    def __init__(self, pairs=()):
        super().__init__(pairs)
        self.decided = set()


def build(players):
    """生成首轮对阵：人数补到下一个 2 的幂，差额全部为轮空。"""
    players = list(players)
    if not players:
        return Bracket()
    size = 1
    while size < len(players):
        size *= 2
    byes = size - len(players)
    pairs = Bracket()
    pos = 0
    for _ in range((len(players) - byes) // 2):
        pairs.append((players[pos], players[pos + 1]))
        pos += 2
    for _ in range(byes):
        pairs.append((players[pos], None))
        pos += 1
    return pairs


def bye_count(players):
    """诊断用：口径要求的轮空人数（下一个 2 的幂 − 人数）。"""
    size = 1
    while size < len(players):
        size *= 2
    return (size - len(players)) % size


def report(pairs, index, winner):
    """上报某场结果：已分出胜负的场次拒绝重复上报。"""
    if index < 0 or index >= len(pairs):
        raise BracketError("没有这一场：%d" % index)
    decided = getattr(pairs, "decided", None)
    if decided is not None and index in decided:
        raise BracketError("第 %d 场已经分出胜负" % index)
    first, second = pairs[index]
    if winner is None or winner not in (first, second):
        raise BracketError("第 %d 场没有这名赢家：%s" % (index, winner))
    pairs[index] = (winner, second if winner == first else first)
    if decided is not None:
        decided.add(index)
    return True
