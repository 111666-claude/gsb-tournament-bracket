# tournament-bracket

淘汰赛对阵：轮空、种子与结果上报，只用 Python 标准库。

```
python3 -m tournamentbracket.cli --sample bye
python3 -m tournamentbracket.cli --sample replay
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **人数不足 2 的幂要补轮空**：5 人报名首轮应有 3 个轮空。`--sample bye` 按口径是
  `bye=3 expect_bye=3`，现在只把落单的 1 人当轮空，给 `bye=1`（还丢了两名轮空选手）。
- **同一场不能重复上报**：已经分出胜负的比赛再上报要返回 `BracketError`。
  `--sample replay`（同一场先报 p1、再报 p2）按口径是 `overwritten=False first=p1`，现在给 `True`。
- **赢家必须在本场里**：不在对阵双方里的名字要报错。
- 不变量：每名选手只出现在一个位置；轮空人数 = 下一个 2 的幂 − 人数；每场结果一旦确定不再变化；
  同一批上报重复处理结果相同。
- 规模：8 万人报名、10 万次上报 1 秒内完成，内存 O(人数)。

## 现在的行为

- `build` 只把落单的最后一人当轮空，不按下一个 2 的幂补齐。
- `report` 不校验该场是否已经结束，直接覆盖结果。

## 输出

```
pairs=4 bye=3 expect_bye=3
overwritten=False first=p1
```

## 目录

```
tournamentbracket/bracket.py   对阵与上报
tournamentbracket/cli.py       命令行入口
tests/                         unittest 用例
```
