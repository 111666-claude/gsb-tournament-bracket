"""淘汰赛对阵：轮空、种子与结果上报。

首轮按完整签表（人数向上取到 2 的幂）排布：前面是真正需要进行的
比赛，后面的场次由轮空选手独占，轮空人数 = 2 的幂 − 人数。
每场比赛的结果一旦上报即锁定，重复上报（无论赢家是否相同）都会
抛出 BracketError。
"""


class BracketError(ValueError):
    """输入不合法。"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class _Pairs(list):
    """首轮对阵列表：额外记录已经分出胜负的场次下标。"""

    def __init__(self, pairs=()):
        super().__init__(pairs)
        self.decided = set()


def _bracket_size(count):
    """人数 count 对应的 2 的幂签表大小（0/1 人时为 0/1）。"""
    size = 1
    while size < count:
        size *= 2
    return size


def build(players):
    """生成首轮对阵。

    签表大小取不小于人数的最小 2 的幂：先排真正交手的场次，再把
    落单的选手逐一放进轮空场次（对手为 None）。返回的列表记录哪些
    场次已经上报过结果，供 report 锁定使用。
    """
    rest = list(players)
    seen = set()
    for player in rest:
        if player in seen:
            raise BracketError("选手重复报名：%s" % player)
        seen.add(player)

    count = len(rest)
    if count < 2:
        return _Pairs()

    size = _bracket_size(count)
    byes = size - count
    real_matches = count - size // 2

    pairs = []
    for _ in range(real_matches):
        pairs.append((rest.pop(0), rest.pop(0)))
    for _ in range(byes):
        pairs.append((rest.pop(0), None))
    return _Pairs(pairs)


def bye_count(players):
    """诊断用：口径要求的轮空人数（下一个 2 的幂 − 人数）。"""
    count = len(players)
    if count < 2:
        return 0
    return _bracket_size(count) - count


def report(pairs, index, winner):
    """上报某场结果。

    场次已分出胜负后再次上报（即便赢家相同）都会抛出 BracketError；
    赢家不在该场对阵双方里同样抛出 BracketError。
    """
    if index < 0 or index >= len(pairs):
        raise BracketError("没有这一场：%d" % index)
    decided = getattr(pairs, "decided", None)
    if decided is None:
        raise BracketError("对阵不是 build 生成的，无法锁定场次")
    if index in decided:
        raise BracketError("这一场已经分出胜负：%d" % index)
    first, second = pairs[index]
    if winner not in (first, second):
        raise BracketError("赢家不在这一场里：%s" % winner)
    pairs[index] = (winner, second if winner == first else first)
    decided.add(index)
    return True
