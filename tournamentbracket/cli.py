"""命令行入口：跑淘汰赛样例。"""

import argparse

from .bracket import BracketError, build, bye_count, report


def build_parser():
    parser = argparse.ArgumentParser(prog="tournament-bracket", description="淘汰赛对阵")
    parser.add_argument("--sample", default="bye", help="bye / replay")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    players = ["p1", "p2", "p3", "p4", "p5"]
    pairs = build(players)
    if args.sample == "bye":
        byes = sum(1 for first, second in pairs if second is None)
        print("pairs=%d bye=%d expect_bye=%d" % (len(pairs), byes, bye_count(players)))
    elif args.sample == "replay":
        report(pairs, 0, "p1")
        overwritten = False
        try:
            report(pairs, 0, "p2")
            overwritten = True
        except BracketError:
            overwritten = False
        print("overwritten=%s first=%s" % (overwritten, pairs[0][0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
