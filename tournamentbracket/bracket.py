"""淘汰赛对阵：轮空、种子与结果上报。

缺陷：人数不是 2 的幂时不补轮空、同一场比赛可以重复上报覆盖结果。
"""


class BracketError(ValueError):
    """输入不合法。缺陷：不带轮次下标。"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


def build(players):
    """生成首轮对阵。缺陷：只把落单的最后一人当轮空，不按 2 的幂补齐。"""
    pairs = []
    rest = list(players)
    while len(rest) >= 2:
        pairs.append((rest.pop(0), rest.pop(0)))
    if rest:
        pairs.append((rest.pop(0), None))
    return pairs


def bye_count(players):
    """诊断用：口径要求的轮空人数（下一个 2 的幂 − 人数）。"""
    size = 1
    while size < len(players):
        size *= 2
    return (size - len(players)) % size


def report(pairs, index, winner):
    """上报某场结果。缺陷：不校验该场是否已经结束，直接覆盖。"""
    if index < 0 or index >= len(pairs):
        raise BracketError("没有这一场：%d" % index)
    first, second = pairs[index]
    if winner not in (first, second):
        raise BracketError("赢家不在这一场里：%s" % winner)
    pairs[index] = (winner, second if winner == first else first)
    return True
